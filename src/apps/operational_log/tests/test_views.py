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

    def test_registry_shows_scoped_summary_and_journal(self) -> None:
        self.client.force_login(self.user)
        response = self.client.get(reverse("operational_log:registry"))
        self.assertEqual(response.status_code, 200)
        text = response.content.decode("utf-8")
        self.assertIn("Оперативные журналы", text)
        self.assertIn("Оперативный журнал сменного персонала", text)
        self.assertIn("Зарегистрированных записей", text)

    def test_detail_shows_both_times_links_and_author_snapshot(self) -> None:
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("operational_log:detail", args=(self.journal.pk,))
        )
        self.assertEqual(response.status_code, 200)
        text = response.content.decode("utf-8")
        for marker in (
            "ХРОНОЛОГИЧЕСКАЯ ЛЕНТА",
            "Событие:",
            "Регистрация:",
            "Целостность подтверждена",
            "КТП-01",
            "ДЕМО-2026-000001",
        ):
            self.assertIn(marker, text)

    def test_ui_is_read_only(self) -> None:
        self.client.force_login(self.user)
        registry = self.client.get(reverse("operational_log:registry")).content.decode(
            "utf-8"
        )
        detail = self.client.get(
            reverse("operational_log:detail", args=(self.journal.pk,))
        ).content.decode("utf-8")
        for forbidden in (
            "Создать запись",
            "Редактировать запись",
            "Аннулировать запись",
            "Исправить запись",
        ):
            self.assertNotIn(forbidden, registry + detail)
