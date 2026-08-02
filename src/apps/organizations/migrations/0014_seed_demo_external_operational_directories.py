from datetime import date

from django.db import migrations


VALID_FROM = date(2026, 1, 1)
VALID_UNTIL = date(2026, 12, 31)


ORGANIZATIONS = (
    (
        "DEMO-ODU-YUG",
        "Филиал АО «СО ЕЭС» ОДУ Юга — демонстрационный справочник",
        "ОДУ Юга",
        "DISPATCH_CENTER",
        "Руководство и оперативно-диспетчерская служба",
    ),
    (
        "DEMO-SK-RDU",
        "Филиал АО «СО ЕЭС» Северокавказское РДУ — демонстрационный справочник",
        "Северокавказское РДУ",
        "DISPATCH_CENTER",
        "Руководство, старшие диспетчеры и диспетчеры",
    ),
    (
        "DEMO-SK-PMES",
        "Филиал ПАО «Россети» СК ПМЭС — демонстрационный справочник",
        "СК ПМЭС",
        "RELATED_GRID",
        "Руководство, ЦУС и оперативный персонал смежных энергообъектов",
    ),
    (
        "DEMO-PS500-NEV",
        "ПС 500 кВ Невинномысск — демонстрационный смежный энергообъект",
        "ПС 500 кВ Невинномысск",
        "RELATED_SITE",
        "Оперативный персонал смежного энергообъекта",
    ),
    (
        "DEMO-KDC-VES",
        "Коммерческий диспетчерский центр ВЭС — демонстрационный справочник",
        "КДЦ ВЭС",
        "COMMERCIAL_DISPATCH",
        "Руководство и коммерческие диспетчеры",
    ),
)


PEOPLE = (
    (
        "DEMO-ODU-YUG",
        "Руководство",
        "Руководитель оперативно-диспетчерской службы",
        "EXT-ODU-001",
        "Северин",
        "Александр",
        "Игоревич",
        "MANAGEMENT",
        "Оперативное взаимодействие по режимам энергосистемы Юга",
        "Запрос и получение оперативной информации, координация диспетчерского взаимодействия",
        "+7 000 100-10-01",
        "Круглосуточный оперативный канал",
    ),
    (
        "DEMO-ODU-YUG",
        "Оперативно-диспетчерская служба",
        "Старший диспетчер",
        "EXT-ODU-002",
        "Ветров",
        "Денис",
        "Павлович",
        "DISPATCH",
        "Диспетчерское управление объектами ОДУ Юга",
        "Ведение оперативных переговоров и передача диспетчерских команд",
        "+7 000 100-10-02",
        "Круглосуточно",
    ),
    (
        "DEMO-SK-RDU",
        "Оперативно-диспетчерская служба",
        "Главный диспетчер",
        "EXT-RDU-001",
        "Архипов",
        "Михаил",
        "Сергеевич",
        "MANAGEMENT",
        "Диспетчерское управление и ведение объектов Северного Кавказа",
        "Координация оперативных переключений и ликвидации технологических нарушений",
        "+7 000 200-20-01",
        "Рабочие дни 08:00–17:00",
    ),
    (
        "DEMO-SK-RDU",
        "Оперативно-диспетчерская служба",
        "Диспетчер",
        "EXT-RDU-002",
        "Лебедева",
        "Марина",
        "Олеговна",
        "DISPATCH",
        "Объекты диспетчерского управления и ведения Северокавказского РДУ",
        "Оперативные переговоры, команды и разрешения в пределах закреплённой зоны",
        "+7 000 200-20-02",
        "Круглосуточно",
    ),
    (
        "DEMO-SK-PMES",
        "Центр управления сетями",
        "Начальник смены ЦУС",
        "EXT-PMES-001",
        "Горин",
        "Виктор",
        "Алексеевич",
        "CONTROL_CENTER",
        "Электросетевой комплекс СК ПМЭС",
        "Оперативные переговоры, координация переключений и работ на смежных объектах",
        "+7 000 300-30-01",
        "Круглосуточно",
    ),
    (
        "DEMO-SK-PMES",
        "Отдел оперативно-технологического управления ЦУС",
        "Диспетчер ЦУС",
        "EXT-PMES-002",
        "Зуева",
        "Наталья",
        "Романовна",
        "CONTROL_CENTER",
        "Сети 220–500 кВ СК ПМЭС",
        "Ведение оперативных переговоров и координация смежных переключений",
        "+7 000 300-30-02",
        "Круглосуточно",
    ),
    (
        "DEMO-PS500-NEV",
        "Оперативный персонал ПС 500 кВ Невинномысск",
        "Дежурный инженер подстанции",
        "EXT-PS500-001",
        "Руднев",
        "Илья",
        "Максимович",
        "RELATED_SITE",
        "ПС 500 кВ Невинномысск и смежные присоединения",
        "Оперативные переговоры, подтверждение состояния оборудования и выполнение согласованных переключений",
        "+7 000 500-50-01",
        "Круглосуточно",
    ),
    (
        "DEMO-KDC-VES",
        "Коммерческая диспетчерская группа",
        "Коммерческий диспетчер",
        "EXT-KDC-001",
        "Соколова",
        "Елена",
        "Вадимовна",
        "COMMERCIAL_DISPATCH",
        "Коммерческая диспетчеризация ВЭС",
        "Приём и передача коммерческих ограничений, планов и подтверждений режима",
        "+7 000 600-60-01",
        "Ежедневно 08:00–20:00",
    ),
)


RZA_ASSIGNMENTS = (
    ("DEMO-006", "IV", "Устройства РЗА до 330 кВ включительно"),
    ("DEMO-014", "III", "Устройства РЗА до 110 кВ включительно"),
    ("DEMO-009", "III", "Устройства РЗА до 110 кВ включительно"),
)


def seed_external_directories(apps, schema_editor):
    Organization = apps.get_model("organizations", "Organization")
    OrganizationOperationalProfile = apps.get_model(
        "organizations",
        "OrganizationOperationalProfile",
    )
    Division = apps.get_model("organizations", "Division")
    Position = apps.get_model("organizations", "Position")
    Employee = apps.get_model("organizations", "Employee")
    EmployeeContactProfile = apps.get_model(
        "organizations",
        "EmployeeContactProfile",
    )
    ExternalOperationalContact = apps.get_model(
        "organizations",
        "ExternalOperationalContact",
    )
    EmployeeSpecialQualification = apps.get_model(
        "organizations",
        "EmployeeSpecialQualification",
    )

    host = Organization.objects.filter(code="DEMO").first()
    if host is None:
        return

    organizations = {}
    for code, name, short_name, relation_kind, scope in ORGANIZATIONS:
        organization, _ = Organization.objects.update_or_create(
            code=code,
            defaults={
                "name": name,
                "short_name": short_name,
                "is_active": True,
            },
        )
        OrganizationOperationalProfile.objects.update_or_create(
            organization=organization,
            defaults={
                "relation_kind": relation_kind,
                "directory_scope": scope,
                "is_active": True,
            },
        )
        organizations[code] = organization

    for (
        organization_code,
        division_name,
        position_name,
        personnel_number,
        last_name,
        first_name,
        middle_name,
        relation_kind,
        operational_scope,
        authority_summary,
        phone,
        schedule,
    ) in PEOPLE:
        organization = organizations[organization_code]
        division_code = f"{organization_code}-{abs(hash(division_name)) % 100000:05d}"
        position_code = f"{organization_code}-{abs(hash(position_name)) % 100000:05d}"
        division, _ = Division.objects.update_or_create(
            organization=organization,
            code=division_code,
            defaults={"name": division_name, "is_active": True},
        )
        position, _ = Position.objects.update_or_create(
            organization=organization,
            code=position_code,
            defaults={
                "name": position_name,
                "is_operational": relation_kind in {
                    "DISPATCH",
                    "OPERATIONAL",
                    "CONTROL_CENTER",
                    "COMMERCIAL_DISPATCH",
                    "RELATED_SITE",
                },
                "is_active": True,
            },
        )
        employee, _ = Employee.objects.update_or_create(
            organization=organization,
            personnel_number=personnel_number,
            defaults={
                "division": division,
                "position": position,
                "workplace": None,
                "last_name": last_name,
                "first_name": first_name,
                "middle_name": middle_name,
                "employment_start": VALID_FROM,
                "employment_end": None,
                "is_active": True,
            },
        )
        EmployeeContactProfile.objects.update_or_create(
            employee=employee,
            defaults={
                "primary_phone": phone,
                "operational_phone": phone,
                "email": "",
                "availability_schedule": schedule,
                "is_round_the_clock": "Круглосуточ" in schedule,
                "note": "DEMO-ONLY / синтетический внешний справочник",
            },
        )
        ExternalOperationalContact.objects.update_or_create(
            employee=employee,
            host_organization=host,
            relation_kind=relation_kind,
            valid_from=VALID_FROM,
            defaults={
                "operational_scope": operational_scope,
                "authority_summary": authority_summary,
                "valid_until": VALID_UNTIL,
                "basis_reference": (
                    "DEMO-ONLY / структура внешнего оперативного списка / "
                    f"{organization.short_name or organization.name} / редакция 2026"
                ),
                "is_active": True,
            },
        )

    for personnel_number, level, scope in RZA_ASSIGNMENTS:
        employee = Employee.objects.filter(
            organization=host,
            personnel_number=personnel_number,
        ).first()
        if employee is None:
            continue
        EmployeeSpecialQualification.objects.update_or_create(
            employee=employee,
            kind="RZA",
            level=level,
            valid_from=VALID_FROM,
            basis_reference=(
                "DEMO-ONLY / структура списка персонала с присвоением "
                "категорий РЗА / редакция 2026"
            ),
            defaults={
                "scope_text": scope,
                "valid_until": VALID_UNTIL,
                "source_file_sha256": "e" * 64,
                "source_row_number": int(personnel_number.rsplit("-", 1)[1]),
                "is_active": True,
            },
        )


def reverse_external_directories(apps, schema_editor):
    Organization = apps.get_model("organizations", "Organization")
    EmployeeSpecialQualification = apps.get_model(
        "organizations",
        "EmployeeSpecialQualification",
    )
    EmployeeSpecialQualification.objects.filter(
        basis_reference__startswith="DEMO-ONLY / структура списка персонала"
    ).delete()
    Organization.objects.filter(
        code__in=[row[0] for row in ORGANIZATIONS]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0013_operational_right_condition_detail"),
    ]

    operations = [
        migrations.RunPython(
            seed_external_directories,
            reverse_external_directories,
        ),
    ]
