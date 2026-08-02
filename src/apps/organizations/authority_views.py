from __future__ import annotations

import json
import unicodedata
from collections import defaultdict
from dataclasses import dataclass

from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from .authority_models import (
    AuthorityDecision,
    AuthorityEvaluationRecord,
    ExternalPersonnelEngagement,
    OperationalAuthorityGrant,
)
from .models import (
    Division,
    Employee,
    EmployeeOperationalRight,
    EmployeeQualification,
    OperationalRightDefinition,
    Organization,
)


@dataclass(frozen=True, slots=True)
class AuthorityEmployeeRow:
    employee: Employee
    qualification: EmployeeQualification | None
    cells: tuple[EmployeeOperationalRight | None, ...]
    published_rights: tuple[EmployeeOperationalRight, ...]
    right_codes: str
    search_text: str
    division_path: str
    conditional_count: int


def _search_token(value: str) -> str:
    return " ".join(
        unicodedata.normalize("NFKC", value or "")
        .casefold()
        .replace("ё", "е")
        .split()
    )


def _effective_rights_prefetch() -> Prefetch:
    today = timezone.localdate()
    queryset = (
        EmployeeOperationalRight.objects.filter(
            is_active=True,
            valid_from__lte=today,
        )
        .filter(Q(valid_until__isnull=True) | Q(valid_until__gte=today))
        .select_related("right_definition")
        .order_by("right_definition__display_order", "right_definition__name")
    )
    return Prefetch(
        "operational_rights",
        queryset=queryset,
        to_attr="published_rights",
    )


def _effective_qualifications_prefetch() -> Prefetch:
    today = timezone.localdate()
    queryset = (
        EmployeeQualification.objects.filter(
            is_active=True,
            valid_from__lte=today,
        )
        .filter(Q(valid_until__isnull=True) | Q(valid_until__gte=today))
        .order_by("-valid_from", "-id")
    )
    return Prefetch(
        "qualifications",
        queryset=queryset,
        to_attr="published_qualifications",
    )


def _division_ancestry(divisions: list[Division]) -> dict[int, tuple[int, ...]]:
    by_id = {item.id: item for item in divisions}
    ancestry: dict[int, tuple[int, ...]] = {}

    def resolve(division_id: int) -> tuple[int, ...]:
        if division_id in ancestry:
            return ancestry[division_id]
        division = by_id[division_id]
        if division.parent_id and division.parent_id in by_id:
            path = (*resolve(division.parent_id), division_id)
        else:
            path = (division_id,)
        ancestry[division_id] = path
        return path

    for division in divisions:
        resolve(division.id)
    return ancestry


def _employee_row(
    employee: Employee,
    rights: list[OperationalRightDefinition],
    ancestry: dict[int, tuple[int, ...]],
) -> AuthorityEmployeeRow:
    published = tuple(employee.published_rights)
    by_definition = {item.right_definition_id: item for item in published}
    qualification = (
        employee.published_qualifications[0]
        if employee.published_qualifications
        else None
    )
    search_parts = [
        employee.full_name,
        employee.position.name,
        employee.division.name,
        employee.workplace.name if employee.workplace_id else "",
        qualification.personnel_category if qualification else "",
        qualification.electrical_safety_group if qualification else "",
        qualification.voltage_scope if qualification else "",
    ]
    search_parts.extend(
        f"{item.right_definition.name} {item.qualifier} "
        f"{item.scope_text} {item.source_reference}"
        for item in published
    )
    return AuthorityEmployeeRow(
        employee=employee,
        qualification=qualification,
        cells=tuple(by_definition.get(item.id) for item in rights),
        published_rights=published,
        right_codes=" ".join(item.right_definition.code for item in published),
        search_text=_search_token(" ".join(search_parts)),
        division_path=" ".join(
            str(item) for item in ancestry.get(employee.division_id, ())
        ),
        conditional_count=sum(
            item.source_marker.strip() != "+" for item in published
        ),
    )


def _division_rows(
    divisions: list[Division],
    employee_rows: list[AuthorityEmployeeRow],
) -> list[dict[str, object]]:
    children: dict[int | None, list[Division]] = defaultdict(list)
    for division in divisions:
        children[division.parent_id].append(division)
    parent_ids = {item.parent_id for item in divisions if item.parent_id}
    for items in children.values():
        items.sort(key=lambda item: (item.id not in parent_ids, item.name))

    direct_rows: dict[int, list[AuthorityEmployeeRow]] = defaultdict(list)
    for row in employee_rows:
        direct_rows[row.employee.division_id].append(row)
    for items in direct_rows.values():
        items.sort(
            key=lambda row: (
                row.employee.position.name,
                row.employee.last_name,
                row.employee.first_name,
            )
        )

    descendant_count: dict[int, int] = {}

    def count_people(division: Division) -> int:
        count = len(direct_rows.get(division.id, ()))
        for child in children.get(division.id, ()):
            count += count_people(child)
        descendant_count[division.id] = count
        return count

    for root in children.get(None, ()):
        count_people(root)

    result: list[dict[str, object]] = []

    def add_branch(
        parent_id: int | None,
        depth: int,
        ancestors: tuple[int, ...],
    ) -> None:
        for division in children.get(parent_id, ()):
            path = (*ancestors, division.id)
            result.append(
                {
                    "division": division,
                    "depth": depth,
                    "ancestor_ids": " ".join(map(str, ancestors)),
                    "division_path": " ".join(map(str, path)),
                    "employee_count": descendant_count.get(division.id, 0),
                    "direct_rows": direct_rows.get(division.id, []),
                }
            )
            add_branch(division.id, depth + 1, path)

    add_branch(None, 0, ())
    return result


def _category_groups(rights: list[OperationalRightDefinition]):
    labels = dict(OperationalRightDefinition.Category.choices)
    groups = []
    current = None
    for right in rights:
        if current is None or current["code"] != right.category:
            current = {
                "code": right.category,
                "name": labels.get(right.category, right.category),
                "rights": [],
            }
            groups.append(current)
        current["rights"].append(right)
    return groups


@login_required
def authority_registry(request):
    today = timezone.localdate()
    organizations = list(
        Organization.objects.filter(
            is_active=True,
            employees__is_active=True,
            employees__operational_rights__is_active=True,
            employees__operational_rights__valid_from__lte=today,
        )
        .filter(
            Q(employees__operational_rights__valid_until__isnull=True)
            | Q(employees__operational_rights__valid_until__gte=today)
        )
        .distinct()
        .order_by("name")
    )
    selected_code = request.GET.get("organization", "").strip()
    selected = next(
        (item for item in organizations if item.code == selected_code),
        None,
    )
    if selected is None:
        selected = next(
            (item for item in organizations if item.code == "DEMO"),
            organizations[0] if organizations else None,
        )

    rights = []
    employee_rows = []
    division_rows = []
    holder_assignments = []
    external_engagements = []
    recent_evaluations = []

    if selected is not None:
        rights = list(
            OperationalRightDefinition.objects.filter(
                is_active=True,
                employee_grants__employee__organization=selected,
                employee_grants__is_active=True,
                employee_grants__valid_from__lte=today,
            )
            .filter(
                Q(employee_grants__valid_until__isnull=True)
                | Q(employee_grants__valid_until__gte=today)
            )
            .distinct()
            .order_by("display_order", "name")
        )
        divisions = list(
            Division.objects.filter(organization=selected, is_active=True)
            .select_related("parent")
            .order_by("name")
        )
        employees = list(
            Employee.objects.filter(organization=selected, is_active=True)
            .select_related("division", "position", "workplace")
            .prefetch_related(
                _effective_rights_prefetch(),
                _effective_qualifications_prefetch(),
            )
            .order_by("division__name", "position__name", "last_name")
        )
        ancestry = _division_ancestry(divisions)
        employee_rows = [
            _employee_row(employee, rights, ancestry)
            for employee in employees
        ]
        division_rows = _division_rows(divisions, employee_rows)
        holder_assignments = [
            {"row": row, "assignment": assignment}
            for row in employee_rows
            for assignment in row.published_rights
        ]
        holder_assignments.sort(
            key=lambda item: (
                item["assignment"].right_definition.display_order,
                item["row"].employee.division.name,
                item["row"].employee.position.name,
                item["row"].employee.last_name,
            )
        )
        external_engagements = list(
            ExternalPersonnelEngagement.objects.filter(
                host_organization=selected,
            )
            .select_related(
                "employee__position",
                "employee__division",
                "home_organization",
                "host_organization",
            )
            .order_by("employee__division__name", "employee__last_name")
        )
        recent_evaluations = list(
            AuthorityEvaluationRecord.objects.filter(organization=selected)
            .select_related(
                "organization",
                "actor__position",
                "actor__division",
                "matched_grant",
            )
            .order_by("-occurred_at", "-id")[:100]
        )

    published_count = sum(len(row.published_rights) for row in employee_rows)
    source_references = sorted(
        {
            item.source_reference
            for row in employee_rows
            for item in row.published_rights
            if item.source_reference
        }
    )
    context = {
        "organizations": organizations,
        "selected_organization": selected,
        "rights": rights,
        "category_groups": _category_groups(rights),
        "employee_rows": employee_rows,
        "division_rows": division_rows,
        "holder_assignments": holder_assignments,
        "external_engagements": external_engagements,
        "recent_evaluations": recent_evaluations,
        "published_right_count": published_count,
        "conditional_count": sum(
            row.conditional_count for row in employee_rows
        ),
        "employees_with_rights": sum(
            bool(row.published_rights) for row in employee_rows
        ),
        "allow_count": sum(
            item.decision == AuthorityDecision.ALLOW
            for item in recent_evaluations
        ),
        "source_references": source_references,
    }
    return render(request, "organizations/authority_registry.html", context)


@login_required
def employee_detail(request, public_id):
    employee = get_object_or_404(
        Employee.objects.select_related(
            "organization",
            "division",
            "position",
            "workplace",
            "user",
        ).prefetch_related(
            _effective_rights_prefetch(),
            _effective_qualifications_prefetch(),
        ),
        public_id=public_id,
        is_active=True,
    )
    qualifications = list(employee.published_qualifications)
    published_rights = list(employee.published_rights)
    structured_grants = list(
        OperationalAuthorityGrant.objects.filter(employee=employee)
        .select_related(
            "right_definition",
            "organization",
            "granting_organization",
            "source_operational_right",
        )
        .order_by("action_code", "scope_kind", "scope_label", "-valid_from")
    )
    structured_by_source = {
        item.source_operational_right_id: item
        for item in structured_grants
        if item.source_operational_right_id
    }
    labels = dict(OperationalRightDefinition.Category.choices)
    grouped_rights = []
    current = None
    for assignment in published_rights:
        category = assignment.right_definition.category
        if current is None or current["code"] != category:
            current = {
                "code": category,
                "name": labels.get(category, category),
                "rights": [],
            }
            grouped_rights.append(current)
        current["rights"].append(
            {
                "assignment": assignment,
                "structured_grant": structured_by_source.get(assignment.id),
            }
        )

    context = {
        "employee": employee,
        "qualifications": qualifications,
        "published_rights": published_rights,
        "grouped_rights": grouped_rights,
        "structured_grants": structured_grants,
        "external_engagements": list(
            ExternalPersonnelEngagement.objects.filter(employee=employee)
            .select_related("home_organization", "host_organization")
            .order_by("-valid_from")
        ),
        "authority_evaluations": list(
            AuthorityEvaluationRecord.objects.filter(actor=employee)
            .select_related("organization", "matched_grant")
            .order_by("-occurred_at", "-id")[:20]
        ),
        "conditional_count": sum(
            item.source_marker.strip() != "+" for item in published_rights
        ),
        "source_references": sorted(
            {
                item.source_reference
                for item in published_rights
                if item.source_reference
            }
        ),
    }
    return render(request, "organizations/employee_detail.html", context)


@login_required
def authority_evaluation_detail(request, public_id):
    evaluation = get_object_or_404(
        AuthorityEvaluationRecord.objects.select_related(
            "organization",
            "actor__position",
            "actor__division",
            "matched_grant__right_definition",
            "previous_evaluation",
            "recorded_by",
        ),
        public_id=public_id,
    )
    return render(
        request,
        "organizations/authority_evaluation_detail.html",
        {
            "evaluation": evaluation,
            "snapshot_json": json.dumps(
                evaluation.snapshot,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            ),
        },
    )
