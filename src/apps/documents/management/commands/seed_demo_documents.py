from __future__ import annotations

from uuid import UUID

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.documents.models import Document, DocumentLink, DocumentType
from apps.documents.services import (
    create_document_draft,
    create_document_link,
    register_document,
)
from apps.organizations.models import Employee, Organization

REGISTERED_ONE_ID = UUID("00000000-0000-4000-8000-000000000301")
REGISTERED_TWO_ID = UUID("00000000-0000-4000-8000-000000000302")
DRAFT_ID = UUID("00000000-0000-4000-8000-000000000303")


class Command(BaseCommand):
    help = "Создаёт вымышленные демонстрационные документы для локального профиля."

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        try:
            organization = Organization.objects.get(code="DEMO")
            actor = Employee.objects.select_related("user").get(
                organization=organization,
                user__username="operator.demo",
            )
        except (Organization.DoesNotExist, Employee.DoesNotExist) as error:
            raise CommandError(
                "Сначала выполните seed_demo_organization --reset-passwords."
            ) from error

        document_type, _ = DocumentType.objects.update_or_create(
            organization=organization,
            code="general",
            defaults={
                "name": "Общий оперативный документ",
                "number_prefix": "ДЕМО",
                "number_width": 6,
                "is_active": True,
            },
        )

        registered_one = self._document(
            public_id=REGISTERED_ONE_ID,
            document_type=document_type,
            actor=actor,
            title="Демонстрационный порядок передачи информации",
            subject="Порядок обмена информацией",
            body=(
                "Вымышленный документ прототипа. Не содержит производственных данных "
                "и не применяется в действующей электроустановке."
            ),
            register=True,
        )
        registered_two = self._document(
            public_id=REGISTERED_TWO_ID,
            document_type=document_type,
            actor=actor,
            title="Демонстрационная памятка оперативному работнику",
            subject="Памятка",
            body=(
                "Тестовая версия для проверки серверной регистрации, неизменяемости "
                "и типизированных связей документов."
            ),
            register=True,
        )
        self._document(
            public_id=DRAFT_ID,
            document_type=document_type,
            actor=actor,
            title="Черновик демонстрационной записи",
            subject="Черновик",
            body="Этот вымышленный черновик можно редактировать и зарегистрировать.",
            register=False,
        )

        if not DocumentLink.objects.filter(
            source_document=registered_two,
            target_document=registered_one,
            link_type=DocumentLink.LinkType.RELATED,
        ).exists():
            create_document_link(
                source_document=registered_two,
                target_document=registered_one,
                link_type=DocumentLink.LinkType.RELATED,
                actor=actor,
            )

        self.stdout.write(self.style.SUCCESS("Демонстрационные документы созданы или проверены."))
        self.stdout.write(f"Тип документа: {document_type.code} / {document_type.number_prefix}")
        self.stdout.write(
            f"Зарегистрировано: {registered_one.registration_number}, "
            f"{registered_two.registration_number}"
        )
        self.stdout.write("Черновиков: 1")

    def _document(
        self,
        *,
        public_id: UUID,
        document_type: DocumentType,
        actor: Employee,
        title: str,
        subject: str,
        body: str,
        register: bool,
    ) -> Document:
        document = Document.objects.filter(public_id=public_id).first()
        if document is None:
            document = create_document_draft(
                document_type=document_type,
                actor=actor,
                title=title,
                content={"subject": subject, "body": body},
                public_id=public_id,
            )
        if register and document.status == Document.Status.DRAFT:
            document = register_document(document=document, actor=actor).document
        return document
