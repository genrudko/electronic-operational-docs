from django.urls import path

from . import views

app_name = "operational_log"

urlpatterns = [
    path("operations/journal/", views.registry, name="registry"),
    path(
        "operations/journal/<int:journal_id>/shift/",
        views.shift_workspace,
        name="shift_workspace",
    ),
    path(
        "operations/journal/<int:journal_id>/shift/open/",
        views.open_shift_view,
        name="open_shift",
    ),
    path(
        "operations/journal/<int:journal_id>/shift/drafts/add/",
        views.add_draft_entry,
        name="add_draft",
    ),
    path(
        (
            "operations/journal/<int:journal_id>/shift/drafts/"
            "<uuid:public_id>/autosave/"
        ),
        views.autosave_draft_entry,
        name="autosave_draft",
    ),
    path(
        (
            "operations/journal/<int:journal_id>/shift/drafts/"
            "<uuid:public_id>/move/"
        ),
        views.move_draft_entry_view,
        name="move_draft",
    ),
    path(
        (
            "operations/journal/<int:journal_id>/shift/drafts/"
            "<uuid:public_id>/remove/"
        ),
        views.remove_draft_entry_view,
        name="remove_draft",
    ),
    path(
        (
            "operations/journal/<int:journal_id>/shift/drafts/"
            "<uuid:public_id>/restore/"
        ),
        views.restore_draft_entry_view,
        name="restore_draft",
    ),
    path(
        "operations/journal/<int:journal_id>/display/",
        views.update_display,
        name="update_display",
    ),
    path(
        "operations/journal/<int:journal_id>/",
        views.detail,
        name="detail",
    ),
]
