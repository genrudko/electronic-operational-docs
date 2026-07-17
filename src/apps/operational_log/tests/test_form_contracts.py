from dataclasses import FrozenInstanceError

from django.test import SimpleTestCase

from apps.operational_log.form_contracts import (
    OPERATIONAL_JOURNAL_FORM,
    OPERATIONAL_JOURNAL_FORM_CODE,
    ApprovedFormColumn,
    ApprovedJournalForm,
    approved_journal_form,
)


class ApprovedJournalFormContractTests(SimpleTestCase):
    def test_operational_journal_has_exact_approved_columns(self) -> None:
        self.assertEqual(
            tuple(column.title for column in OPERATIONAL_JOURNAL_FORM.columns),
            (
                "Дата и время записи",
                "Содержание записей в течение смены, подписи о приемке и сдаче смены",
                "Визы и замечания административно-технического персонала",
            ),
        )

    def test_operational_journal_columns_preserve_order_and_width(self) -> None:
        self.assertEqual(
            tuple(column.key for column in OPERATIONAL_JOURNAL_FORM.columns),
            ("date_time", "message", "visas"),
        )
        self.assertEqual(
            tuple(column.width_percent for column in OPERATIONAL_JOURNAL_FORM.columns),
            (14, 66, 20),
        )
        self.assertEqual(
            sum(column.width_percent for column in OPERATIONAL_JOURNAL_FORM.columns),
            100,
        )

    def test_local_instruction_is_the_form_source(self) -> None:
        self.assertIn("И-00-007-ОР-2025", OPERATIONAL_JOURNAL_FORM.source_reference)
        self.assertIn("приложение № 2", OPERATIONAL_JOURNAL_FORM.source_reference)

    def test_registered_contract_is_resolved_by_stable_code(self) -> None:
        self.assertIs(
            approved_journal_form(OPERATIONAL_JOURNAL_FORM_CODE),
            OPERATIONAL_JOURNAL_FORM,
        )

    def test_unknown_form_code_is_rejected(self) -> None:
        with self.assertRaises(KeyError):
            approved_journal_form("unknown-form")

    def test_contract_is_immutable_and_rejects_invalid_columns(self) -> None:
        with self.assertRaises(FrozenInstanceError):
            OPERATIONAL_JOURNAL_FORM.title = "Подменённая форма"  # type: ignore[misc]

        invalid = ApprovedJournalForm(
            code="invalid",
            title="Некорректная форма",
            source_title="Источник",
            source_reference="Реквизиты",
            columns=(
                ApprovedFormColumn("date", "Дата", 60),
                ApprovedFormColumn("date", "Повтор", 30),
            ),
        )
        with self.assertRaises(ValueError):
            invalid.validate()
