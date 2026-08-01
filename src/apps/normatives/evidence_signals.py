from __future__ import annotations

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.documents.models import DocumentSignature

from .evidence_services import record_document_signature_evidence


@receiver(
    post_save,
    sender=DocumentSignature,
    dispatch_uid="normatives.record_document_signature_evidence",
)
def document_signature_created(
    sender: type[DocumentSignature],
    instance: DocumentSignature,
    created: bool,
    raw: bool,
    **kwargs: object,
) -> None:
    if raw or not created:
        return
    record_document_signature_evidence(signature=instance)
