from datetime import date

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.organizations.models import Employee, Organization

from ...models import (
    NormativeDocument,
    NormativeRequirement,
    NormativeRevision,
    OrganizationConfigurationRevision,
    OrganizationNameRevision,
    PublicationStatus,
    RequirementTrace,
)
from ...services import (
    publish_configuration_revision,
    publish_normative_revision,
    publish_organization_name_revision,
)


class Command(BaseCommand):
    help = "Создаёт обезличенный демонстрационный нормативный реестр."

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        call_command("seed_demo_organization", verbosity=0)
        organization = Organization.objects.get(code="DEMO")
        actor = Employee.objects.select_related("user").get(user__username="operator.demo")

        document, _ = NormativeDocument.objects.update_or_create(
            code="demo-electronic-documentation",
            defaults={
                "organization": None,
                "title": (
                    "Правила технической эксплуатации электрических станций "
                    "и сетей Российской Федерации"
                ),
                "short_title": "ПТЭ электрических станций и сетей",
                "scope": NormativeDocument.Scope.FEDERAL,
                "issuer": "Министерство энергетики Российской Федерации (Минэнерго России)",
                "document_number": "Приказ Минэнерго России от 04.10.2022 № 1070",
                "document_date": date(2022, 10, 4),
                "is_active": True,
            },
        )
        revision, _ = NormativeRevision.objects.get_or_create(
            document=document,
            revision_number=1,
            defaults={
                "effective_from": date(2023, 3, 1),
                "source_reference": (
                    "Публичное наименование ПТЭ; требования профиля "
                    "сформулированы для демонстрации"
                ),
                "change_summary": (
                    "Презентационная нормативная матрица "
                    "оперативно-технологического управления."
                ),
            },
        )
        if revision.status == PublicationStatus.DRAFT:
            requirements = (
                (
                    "PTE-57-OPTECH",
                    "п. 57",
                    "Организация оперативно-технологического управления",
                    (
                        "В отношении каждого объекта электроэнергетики владельцем "
                        "должно быть организовано оперативно-технологическое управление."
                    ),
                    "Объекты электроэнергетики презентационного профиля.",
                    10,
                ),
                (
                    "PTE-67-METHODS",
                    "п. 67",
                    "Способы оперативно-технологического управления",
                    (
                        "ЛЭП, оборудование и устройства распределяются по "
                        "технологическому управлению и технологическому ведению."
                    ),
                    "Реестр управления и ведения оборудования.",
                    20,
                ),
                (
                    "PTE-68-DISTRIBUTION",
                    "п. 68",
                    "Единственность управления и допустимость ведения",
                    (
                        "Для объекта допускается одно технологическое управление "
                        "соответствующего уровня; технологическое ведение может быть "
                        "назначено нескольким субъектам в установленных случаях."
                    ),
                    "Проверка конфликтов опубликованных назначений.",
                    30,
                ),
            )
            for code, clause, title, requirement_text, applicability, order in requirements:
                NormativeRequirement.objects.update_or_create(
                    revision=revision,
                    code=code,
                    defaults={
                        "clause": clause,
                        "title": title,
                        "requirement_text": requirement_text,
                        "applicability_text": applicability,
                        "is_mandatory": True,
                        "display_order": order,
                    },
                )
            revision = publish_normative_revision(revision=revision, actor=actor)

        trace_data = (
            (
                "PTE-57-OPTECH",
                "DISPATCH-REGISTRY",
                "Реестр оперативно-технологического управления",
                "apps.dispatching.tests.test_views.DispatchingViewTests",
            ),
            (
                "PTE-67-METHODS",
                "DISPATCH-METHODS",
                "Раздельное моделирование управления и ведения",
                "apps.dispatching.tests.test_models.DispatchingModelTests",
            ),
            (
                "PTE-68-DISTRIBUTION",
                "DISPATCH-CONFLICTS",
                "Контроль единственного активного управления на уровне",
                "apps.dispatching.tests.test_services.DispatchingServiceTests",
            ),
        )
        for requirement_code, function_code, function_name, test_reference in trace_data:
            requirement = revision.requirements.get(code=requirement_code)
            if not requirement.traces.filter(
                function_code=function_code,
                test_reference=test_reference,
            ).exists():
                RequirementTrace.objects.create(
                    requirement=requirement,
                    function_code=function_code,
                    function_name=function_name,
                    implementation_status=RequirementTrace.ImplementationStatus.VERIFIED,
                    test_reference=test_reference,
                    acceptance_scenario=(
                        "Открыть нормативную редакцию и проверить наличие функции, "
                        "автоматического теста и понятного пользовательского описания."
                    ),
                )

        first_name, _ = OrganizationNameRevision.objects.get_or_create(
            organization=organization,
            valid_from=date(2024, 1, 1),
            defaults={
                "full_name": "Акционерное общество «Демонстрационная ветроэнергетика»",
                "short_name": "АО «ДемоВетер»",
                "valid_until": date(2025, 12, 31),
                "basis_reference": "Учебное решение о переименовании № 1",
                "created_by": actor,
            },
        )
        if first_name.status == PublicationStatus.DRAFT:
            publish_organization_name_revision(revision=first_name, actor=actor)

        current_name, _ = OrganizationNameRevision.objects.get_or_create(
            organization=organization,
            valid_from=date(2026, 1, 1),
            defaults={
                "full_name": "Акционерное общество «Демонстрационная энергия»",
                "short_name": "АО «ДемоЭнергия»",
                "valid_until": None,
                "basis_reference": "Учебное решение о переименовании № 2",
                "created_by": actor,
            },
        )
        if current_name.status == PublicationStatus.DRAFT:
            publish_organization_name_revision(revision=current_name, actor=actor)

        configuration, _ = OrganizationConfigurationRevision.objects.get_or_create(
            organization=organization,
            revision_number=1,
            defaults={
                "effective_from": date(2026, 1, 1),
                "effective_until": None,
                "configuration": {
                    "profile": "демонстрационная ВЭС",
                    "modules": {
                        "documents": True,
                        "normatives": True,
                        "equipment": False,
                    },
                    "language": "ru",
                },
                "change_summary": "Первая опубликованная демонстрационная конфигурация.",
                "created_by": actor,
            },
        )
        if configuration.status == PublicationStatus.DRAFT:
            publish_configuration_revision(revision=configuration, actor=actor)

        self.stdout.write(self.style.SUCCESS("Демонстрационный нормативный реестр создан или проверен."))
        self.stdout.write(f"Нормативных документов: {NormativeDocument.objects.count()}")
        self.stdout.write(
            f"Опубликованных редакций: "
            f"{NormativeRevision.objects.filter(status=PublicationStatus.PUBLISHED).count()}"
        )
        self.stdout.write(f"Требований: {NormativeRequirement.objects.count()}")
