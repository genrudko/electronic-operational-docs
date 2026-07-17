from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True, slots=True)
class ApprovedFormColumn:
    key: str
    title: str
    width_percent: int


@dataclass(frozen=True, slots=True)
class ApprovedJournalForm:
    code: str
    title: str
    source_title: str
    source_reference: str
    columns: tuple[ApprovedFormColumn, ...]
    print_orientation: str = "landscape"

    def validate(self) -> None:
        if not self.code.strip():
            raise ValueError("Код утверждённой формы обязателен.")
        if not self.title.strip():
            raise ValueError("Наименование утверждённой формы обязательно.")
        if not self.source_title.strip() or not self.source_reference.strip():
            raise ValueError("Для утверждённой формы требуется источник.")
        if not self.columns:
            raise ValueError("Утверждённая форма должна содержать графы.")

        keys = [column.key for column in self.columns]
        if len(keys) != len(set(keys)):
            raise ValueError("Ключи граф утверждённой формы не должны повторяться.")
        if any(
            not column.key.strip() or not column.title.strip() or column.width_percent <= 0
            for column in self.columns
        ):
            raise ValueError("Каждая графа должна иметь ключ, заголовок и ширину.")
        if sum(column.width_percent for column in self.columns) != 100:
            raise ValueError("Сумма ширины граф утверждённой формы должна быть равна 100%.")
        if self.print_orientation not in {"portrait", "landscape"}:
            raise ValueError("Неизвестная ориентация печатной формы.")


OPERATIONAL_JOURNAL_FORM_CODE: Final = "operational-journal.standard-three-column.v1"

OPERATIONAL_JOURNAL_FORM: Final = ApprovedJournalForm(
    code=OPERATIONAL_JOURNAL_FORM_CODE,
    title="Оперативный журнал",
    source_title="Утверждённая форма оперативного журнала",
    source_reference=("Инструктивное письмо Минтопэнерго России от 09.11.1995 № 42-6/35-ЭТ, приложение 1"),
    columns=(
        ApprovedFormColumn(
            key="date_time",
            title="Дата, время",
            width_percent=16,
        ),
        ApprovedFormColumn(
            key="message",
            title=("Содержание сообщений в течение смены, подписи о сдаче и приемке смены"),
            width_percent=68,
        ),
        ApprovedFormColumn(
            key="visas",
            title="Визы, замечания",
            width_percent=16,
        ),
    ),
)

APPROVED_JOURNAL_FORMS: Final = {
    OPERATIONAL_JOURNAL_FORM.code: OPERATIONAL_JOURNAL_FORM,
}

for approved_form in APPROVED_JOURNAL_FORMS.values():
    approved_form.validate()


def approved_journal_form(code: str) -> ApprovedJournalForm:
    try:
        return APPROVED_JOURNAL_FORMS[code]
    except KeyError as error:
        raise KeyError(f"Не зарегистрирована утверждённая форма журнала: {code}") from error
