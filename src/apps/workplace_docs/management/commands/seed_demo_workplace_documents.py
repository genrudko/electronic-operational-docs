from datetime import date

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.normatives.models import NormativeDocument
from apps.organizations.models import Employee, Organization, Workplace

from ...models import (
    RequirementKind,
    RevisionStatus,
    SourceKind,
    StorageForm,
    WorkplaceDocumentEntry,
    WorkplaceDocumentList,
    WorkplaceDocumentRevision,
)
from ...services import approve_revision


class Command(BaseCommand):
    help = "Создаёт безопасный демонстрационный перечень документации рабочего места."

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        call_command("seed_demo_normatives", verbosity=0)
        organization = Organization.objects.get(code="DEMO")
        workplace = Workplace.objects.get(organization=organization, code="SHIFT_POOL")
        actor = Employee.objects.select_related("position").get(user__username="supervisor.demo")
        normative = NormativeDocument.objects.get(code="demo-electronic-documentation")

        document_list, _ = WorkplaceDocumentList.objects.update_or_create(
            organization=organization,
            code="shift-workplace-documentation",
            defaults={
                "workplace": workplace,
                "title": "Перечень документации сменного персонала",
                "is_active": True,
            },
        )
        revision, _ = WorkplaceDocumentRevision.objects.get_or_create(
            document_list=document_list,
            revision_number=1,
            defaults={
                "effective_from": date(2026, 1, 1),
                "effective_until": None,
                "review_period_months": 12,
                "change_summary": (
                    "Первая утверждённая демонстрационная редакция перечня "
                    "документации сменного персонала."
                ),
            },
        )
        if revision.status == RevisionStatus.DRAFT:
            rows = (
                (
                    "OP-JOURNAL",
                    "Оперативный журнал",
                    SourceKind.LOCAL,
                    RequirementKind.MANDATORY,
                    "На каждом дежурстве сменного оперативного персонала.",
                    StorageForm.ELECTRONIC,
                    None,
                    "Локальный порядок ведения оперативной документации.",
                    10,
                ),
                (
                    "SHIFT-HANDOVER",
                    "Материалы приёма и сдачи смены",
                    SourceKind.LOCAL,
                    RequirementKind.MANDATORY,
                    "При каждой передаче смены между оперативными работниками.",
                    StorageForm.ELECTRONIC,
                    None,
                    "Локальная инструкция по организации дежурства.",
                    20,
                ),
                (
                    "ORDERS",
                    "Журнал распоряжений",
                    SourceKind.LOCAL,
                    RequirementKind.MANDATORY,
                    "Для регистрации распоряжений, относящихся к работе смены.",
                    StorageForm.PAPER,
                    None,
                    "Локальный порядок выдачи и регистрации распоряжений.",
                    30,
                ),
                (
                    "SWITCHING",
                    "Бланки и программы переключений",
                    SourceKind.LOCAL,
                    RequirementKind.CONDITIONAL,
                    "При подготовке и выполнении переключений, требующих бланка или программы.",
                    StorageForm.MIXED,
                    None,
                    "Локальная инструкция по переключениям.",
                    40,
                ),
                (
                    "DEFECTS",
                    "Журнал дефектов оборудования",
                    SourceKind.LOCAL,
                    RequirementKind.MANDATORY,
                    "Для фиксации выявленных дефектов и контроля их состояния.",
                    StorageForm.ELECTRONIC,
                    None,
                    "Локальный порядок учёта дефектов оборудования.",
                    50,
                ),
                (
                    "PTE",
                    "Правила технической эксплуатации электрических станций и сетей",
                    SourceKind.TYPICAL,
                    RequirementKind.MANDATORY,
                    "Для оперативно-технологического управления объектами электроэнергетики.",
                    StorageForm.ELECTRONIC,
                    normative,
                    "",
                    60,
                ),
                (
                    "EQUIPMENT-INSTRUCTIONS",
                    "Эксплуатационные инструкции по закреплённому оборудованию",
                    SourceKind.LOCAL,
                    RequirementKind.CONDITIONAL,
                    "В составе, соответствующем оборудованию и зоне обслуживания рабочего места.",
                    StorageForm.MIXED,
                    None,
                    "Действующие локальные эксплуатационные инструкции.",
                    70,
                ),
            )
            for (
                code,
                title,
                source_kind,
                requirement_kind,
                applicability,
                storage_form,
                normative_document,
                basis_text,
                display_order,
            ) in rows:
                WorkplaceDocumentEntry.objects.update_or_create(
                    revision=revision,
                    code=code,
                    defaults={
                        "title": title,
                        "source_kind": source_kind,
                        "requirement_kind": requirement_kind,
                        "applicability_text": applicability,
                        "storage_form": storage_form,
                        "normative_document": normative_document,
                        "normative_clause": "" if normative_document is None else "Общие требования",
                        "basis_text": basis_text,
                        "notes": "",
                        "display_order": display_order,
                    },
                )
            revision = approve_revision(revision=revision, actor=actor)

        self.stdout.write(
            self.style.SUCCESS("Демонстрационный перечень документации создан или проверен.")
        )
        self.stdout.write(f"Перечней: {WorkplaceDocumentList.objects.count()}")
        self.stdout.write(
            "Утверждённых редакций: "
            f"{WorkplaceDocumentRevision.objects.filter(status=RevisionStatus.APPROVED).count()}"
        )
        self.stdout.write(f"Позиций: {WorkplaceDocumentEntry.objects.count()}")
