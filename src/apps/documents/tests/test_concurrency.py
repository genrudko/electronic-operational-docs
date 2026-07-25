from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import skipUnless

from django.db import close_old_connections, connection, connections
from django.test import TransactionTestCase, override_settings

from apps.documents.models import Document
from apps.documents.services import create_document_draft, register_demo_document
from apps.organizations.models import Employee

from .factories import document_context


@skipUnless(
    connection.vendor == "postgresql",
    "Полноценная конкурентная проверка серверного нумератора выполняется на PostgreSQL.",
)
@override_settings(DEBUG=True)
class PostgreSQLConcurrentNumberingTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self) -> None:
        self.employee, _, self.document_type = document_context(code="CONCURRENT")
        self.documents = [
            create_document_draft(
                document_type=self.document_type,
                actor=self.employee,
                title=f"Параллельный документ {index}",
                content={"body": f"Содержимое {index}"},
            )
            for index in range(4)
        ]

    def test_parallel_registration_allocates_unique_numbers(self):
        barrier = Barrier(len(self.documents))

        def worker(document_pk: int) -> str:
            close_old_connections()
            try:
                document = Document.objects.get(pk=document_pk)
                actor = Employee.objects.get(pk=self.employee.pk)
                barrier.wait(timeout=10)
                return register_demo_document(document=document, actor=actor).registration_number
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=len(self.documents)) as executor:
            numbers = list(executor.map(worker, [item.pk for item in self.documents]))

        self.assertEqual(len(numbers), len(set(numbers)))
        self.assertEqual(
            sorted(
                Document.objects.filter(pk__in=[item.pk for item in self.documents]).values_list(
                    "sequence_number",
                    flat=True,
                )
            ),
            [1, 2, 3, 4],
        )
