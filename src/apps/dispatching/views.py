from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render

from apps.equipment.models import EquipmentAsset
from apps.equipment.services import dispatcher_name_on

from .models import AdjacentSubjectRelation, DispatchLevel, DispatchSubject
from .services import (
    current_adjacent_revision,
    current_management_revisions,
    current_supervision_revisions,
    dispatching_registry_rows,
    require_dispatching_employee,
)


@login_required
def registry(request: HttpRequest) -> HttpResponse:
    employee = require_dispatching_employee(request.user)
    query = request.GET.get("q", "").strip()
    level_type = request.GET.get("level_type", "").strip()
    rows = dispatching_registry_rows(
        organization=employee.organization,
        query=query,
        level_type=level_type,
    )
    return render(
        request,
        "dispatching/registry.html",
        {
            "employee": employee,
            "rows": rows,
            "query": query,
            "level_type": level_type,
            "level_types": DispatchLevel.LevelType.choices,
            "management_count": sum(len(row["management"]) for row in rows),
            "supervision_count": sum(len(row["supervision"]) for row in rows),
            "information_count": sum(item.is_information_only for row in rows for item in row["supervision"]),
        },
    )


@login_required
def equipment_detail(request: HttpRequest, public_id) -> HttpResponse:
    employee = require_dispatching_employee(request.user)
    equipment = get_object_or_404(
        EquipmentAsset.objects.select_related(
            "organization",
            "site",
            "equipment_type",
            "management_object",
            "supervision_object",
        ),
        organization=employee.organization,
        public_id=public_id,
    )
    management_object = getattr(equipment, "management_object", None)
    supervision_object = getattr(equipment, "supervision_object", None)
    management_history = (
        management_object.revisions.select_related("level", "subject", "published_by").all()
        if management_object is not None
        else []
    )
    supervision_history = (
        supervision_object.revisions.select_related("level", "subject", "published_by").all()
        if supervision_object is not None
        else []
    )
    return render(
        request,
        "dispatching/equipment_detail.html",
        {
            "equipment": equipment,
            "display_name": dispatcher_name_on(equipment),
            "current_management": (
                current_management_revisions(management_object) if management_object is not None else []
            ),
            "current_supervision": (
                current_supervision_revisions(supervision_object) if supervision_object is not None else []
            ),
            "management_history": management_history,
            "supervision_history": supervision_history,
        },
    )


@login_required
def subjects(request: HttpRequest) -> HttpResponse:
    employee = require_dispatching_employee(request.user)
    subject_rows = DispatchSubject.objects.filter(organization=employee.organization).order_by(
        "subject_type", "name"
    )
    relation_rows = []
    relations = AdjacentSubjectRelation.objects.filter(
        organization=employee.organization,
        is_active=True,
    ).select_related("source_subject", "target_subject")
    for relation in relations:
        relation_rows.append(
            {
                "relation": relation,
                "revision": current_adjacent_revision(relation),
            }
        )
    return render(
        request,
        "dispatching/subjects.html",
        {
            "subjects": subject_rows,
            "relation_rows": relation_rows,
        },
    )
