from __future__ import annotations

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import EmployeeOperationalRight
from .personnel_reference_models import OperationalRightConditionDetail


SOURCE_903N = (
    "Правила по охране труда при эксплуатации электроустановок, "
    "утверждённые приказом Минтруда России от 15.12.2020 № 903н"
)

CONDITION_CATALOG = {
    "+1": {
        "title": "Условие по пункту 5.4 Правил по охране труда",
        "description": (
            "Право применяется в соответствии с пунктом 5.4 Правил по охране "
            "труда при эксплуатации электроустановок."
        ),
        "source_clause": "пункт 5.4",
        "source_reference": SOURCE_903N,
    },
    "+2": {
        "title": "Условие по пункту 5.13 Правил по охране труда",
        "description": (
            "Право применяется в соответствии с пунктом 5.13 Правил по охране "
            "труда при эксплуатации электроустановок."
        ),
        "source_clause": "пункт 5.13",
        "source_reference": SOURCE_903N,
    },
}


def sync_condition_detail(right: EmployeeOperationalRight) -> None:
    marker = right.source_marker.strip()
    if marker == "+" or not marker:
        OperationalRightConditionDetail.objects.filter(right=right).delete()
        return

    catalog = CONDITION_CATALOG.get(marker)
    if catalog:
        description = catalog["description"]
        if right.qualifier and right.qualifier not in description:
            description = f"{description} Уточнение публикации: {right.qualifier}"
        defaults = {
            **catalog,
            "description": description,
            "marker": marker,
            "is_resolved": True,
        }
    else:
        qualifier = right.qualifier.strip()
        defaults = {
            "marker": marker,
            "title": f"Дополнительное условие {marker}",
            "description": (
                qualifier
                or "Текст условия в опубликованной редакции не расшифрован."
            ),
            "source_clause": "",
            "source_reference": right.source_reference,
            "is_resolved": bool(qualifier),
        }
    OperationalRightConditionDetail.objects.update_or_create(
        right=right,
        defaults=defaults,
    )


@receiver(post_save, sender=EmployeeOperationalRight)
def employee_right_condition_sync(
    sender,
    instance: EmployeeOperationalRight,
    **kwargs,
) -> None:
    sync_condition_detail(instance)
