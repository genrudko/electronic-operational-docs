from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from .base import OperationalLogTestCase


class OperationalLogViewTests(OperationalLogTestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.user = get_user_model().objects.get(username="operator.demo")

    def test_registry_requires_authentication(self) -> None:
        response = self.client.get(reverse("operational_log:registry"))
        self.assertEqual(response.status_code, 302)

    def test_registry_shows_journal_and_approved_form_source(self) -> None:
        self.client.force_login(self.user)
        response = self.client.get(reverse("operational_log:registry"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Оперативные журналы")
        self.assertContains(response, "Оперативный журнал сменного персонала")
        self.assertContains(response, "Утверждённая форма является обязательным контрактом")
        self.assertContains(response, "№ 42-6/35-ЭТ")

    def test_detail_uses_exact_three_column_approved_form(self) -> None:
        self.client.force_login(self.user)
        response = self.client.get(reverse("operational_log:detail", args=(self.journal.pk,)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Дата, время")
        self.assertContains(
            response,
            ("Содержание сообщений в течение смены, подписи о сдаче и приемке смены"),
        )
        self.assertContains(response, "Визы, замечания")
        self.assertEqual(response.content.count(b'<th scope="col">'), 3)
        self.assertEqual(len(response.context["form_contract"].columns), 3)

    def test_detail_preserves_chronological_order_and_links(self) -> None:
        self.client.force_login(self.user)
        response = self.client.get(reverse("operational_log:detail", args=(self.journal.pk,)))
        text = response.content.decode("utf-8")
        self.assertLess(
            text.index("Демонстрационное дежурство начато"),
            text.index("Получена вымышленная информация"),
        )
        for marker in (
            "КТП-01",
            "ДЕМО-2026-000001",
            "Автор записи:",
            "№ 1",
            "№ 5",
        ):
            self.assertIn(marker, text)

    def test_detail_does_not_replace_form_with_audit_cards(self) -> None:
        self.client.force_login(self.user)
        response = self.client.get(reverse("operational_log:detail", args=(self.journal.pk,)))
        text = response.content.decode("utf-8")
        for forbidden in (
            "ХРОНОЛОГИЧЕСКАЯ ЛЕНТА",
            "Типизированных",
            "Свободных",
            "Целостность подтверждена",
            "Событие:",
            "Регистрация:",
            "operational-entry",
        ):
            self.assertNotIn(forbidden, text)

    def test_detail_has_print_contract_and_hides_technical_data_by_default(self) -> None:
        self.client.force_login(self.user)
        response = self.client.get(reverse("operational_log:detail", args=(self.journal.pk,)))
        self.assertContains(response, "Печать формы")
        self.assertContains(response, "data-approved-journal-form=")
        self.assertContains(response, "approved-journal-table")
        self.assertNotContains(response, "Технические реквизиты зарегистрированных записей")
        self.assertNotContains(response, "SHA-256")

    def test_ui_remains_read_only(self) -> None:
        self.client.force_login(self.user)
        registry = self.client.get(reverse("operational_log:registry")).content.decode("utf-8")
        detail = self.client.get(reverse("operational_log:detail", args=(self.journal.pk,))).content.decode(
            "utf-8"
        )
        for forbidden in (
            "Создать запись",
            "Редактировать запись",
            "Аннулировать запись",
            "Исправить запись",
        ):
            self.assertNotIn(forbidden, registry + detail)
