from __future__ import annotations

from django import template

register = template.Library()


_ACTION_LABELS = {
    "SWITCHING.EXECUTE": "Выполнение переключений",
    "SWITCHING.CONTROL": "Контроль переключений",
    "SWITCHING.AUTHORIZE": "Разрешение на выполнение переключений",
    "EQUIPMENT.INSPECT": "Единоличный осмотр оборудования",
}

_REASON_LABELS = {
    "EXPLICIT_GRANT": "Найдено действующее подтверждённое право.",
    "EMPLOYEE_INACTIVE": "Сотрудник отмечен как неактивный.",
    "EMPLOYMENT_NOT_EFFECTIVE": "Трудовые отношения не действовали в момент проверки.",
    "TENANT_MISMATCH": "Сотрудник относится к другой организации.",
    "NO_MATCHING_GRANT": "Подходящее действующее право не найдено.",
    "GRANT_INACTIVE": "Предоставленное право отключено.",
    "GRANT_NOT_EFFECTIVE": "Срок действия права не охватывает момент проверки.",
    "SCOPE_MISMATCH": "Право не распространяется на выбранный объект или область.",
    "BASIS_VERIFY": "Документ-основание ещё требует подтверждения.",
    "BASIS_REJECTED": "Документ-основание отклонён.",
    "QUALIFICATION_MISSING": "Не подтверждена требуемая квалификация.",
    "EXTERNAL_ENGAGEMENT_REQUIRED": "Для внешнего сотрудника не зарегистрирован допуск принимающей организации.",
    "EXTERNAL_ENGAGEMENT_NOT_EFFECTIVE": "Срок внешнего допуска не охватывает момент проверки.",
    "EXTERNAL_SCOPE_MISMATCH": "Внешний допуск не распространяется на выбранный объект или область.",
    "SUBSTITUTION_NOT_ALLOWED": "Замещение не даёт права на это действие.",
    "SUBSTITUTION_NOT_EFFECTIVE": "Замещение не действовало в момент проверки.",
    "SUBSTITUTION_SCOPE_MISMATCH": "Замещение не распространяется на выбранный объект или область.",
}

_SUBJECT_LABELS = {
    "DEMO-AUTH-ALLOW": "Выполнение переключений по демонстрационному сценарию",
    "DEMO-AUTH-DENY": "Выполнение переключений без подходящего действующего права",
    "DEMO-AUTH-VERIFY": "Разрешение на переключения по основанию, требующему подтверждения",
    "DEMO-AUTH-EXTERNAL": "Единоличный осмотр оборудования подрядным персоналом",
}

_BASIS_LABELS = {
    "EXECUTION-AUTHORITY": "Приказ о предоставлении права на выполнение переключений",
    "CONTROL-AUTHORITY": "Приказ о предоставлении права на контроль переключений",
    "UNCONFIRMED-AUTHORITY": "Проект приказа о предоставлении права на разрешение переключений",
    "CONTRACTOR-ADMISSION": "Допуск подрядной организации к единоличному осмотру",
}

_DECISION_HEADINGS = {
    "ALLOW": "Действие разрешено",
    "DENY": "Действие запрещено",
    "VERIFY": "Нужно подтверждение ответственного лица",
}

_DECISION_EXPLANATIONS = {
    "ALLOW": "На момент действия найдено подходящее право с подтверждённым основанием и действующей областью.",
    "DENY": "На момент действия обязательные условия полномочия не выполнены.",
    "VERIFY": "Система не может подтвердить право автоматически: требуется проверить документ-основание или исходные сведения.",
}


@register.filter
def authority_action_label(value: object) -> str:
    code = str(value or "").strip().upper()
    return _ACTION_LABELS.get(code, code.replace("_", " ").replace(".", " · ").title())


@register.filter
def authority_reason_label(value: object) -> str:
    code = str(value or "").strip().upper()
    return _REASON_LABELS.get(code, code.replace("_", " ").capitalize())


@register.filter
def authority_subject_label(value: object) -> str:
    subject_id = str(value or "").strip()
    return _SUBJECT_LABELS.get(subject_id, subject_id.replace("_", " "))


@register.filter
def authority_basis_label(value: object) -> str:
    raw = " ".join(str(value or "").split())
    for marker, label in _BASIS_LABELS.items():
        if marker in raw.upper():
            suffix = " (демонстрационные данные)" if "DEMO-ONLY" in raw.upper() else ""
            if marker == "UNCONFIRMED-AUTHORITY":
                suffix = " — требует подтверждения"
            return f"{label}{suffix}"
    return raw


@register.filter
def authority_decision_heading(value: object) -> str:
    return _DECISION_HEADINGS.get(str(value or "").upper(), "Результат проверки")


@register.filter
def authority_decision_explanation(value: object) -> str:
    return _DECISION_EXPLANATIONS.get(str(value or "").upper(), "Результат сформирован по сведениям, действовавшим в момент проверки.")


@register.filter
def authority_decision_tone(value: object) -> str:
    return {
        "ALLOW": "allowed",
        "DENY": "denied",
        "VERIFY": "verify",
    }.get(str(value or "").upper(), "neutral")


@register.filter
def authority_basis_tone(value: object) -> str:
    return {
        "CONFIRMED": "allowed",
        "VERIFY": "verify",
        "REJECTED": "denied",
    }.get(str(value or "").upper(), "neutral")
