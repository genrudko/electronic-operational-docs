from django.urls import path

from . import views

app_name = "normatives"

urlpatterns = [
    path("normatives/", views.registry, name="registry"),
    path("normatives/evidence/", views.evidence_registry, name="evidence_registry"),
    path(
        "normatives/evidence/legal-modes/<uuid:public_id>/",
        views.legal_mode_decision_detail,
        name="legal_mode_decision_detail",
    ),
    path(
        "normatives/evidence/events/<uuid:public_id>/",
        views.evidence_event_detail,
        name="evidence_event_detail",
    ),
    path("normatives/<slug:code>/", views.document_detail, name="document_detail"),
    path(
        "normatives/<slug:code>/revisions/<int:revision_number>/",
        views.revision_detail,
        name="revision_detail",
    ),
]
