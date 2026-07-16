from __future__ import annotations

import io
import zipfile
from datetime import date

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.imports.models import ImportBatch, ImportEvent, ImportRow
from apps.imports.services import (
    create_import_batch,
    discard_import_batch,
    normalize_cell,
)
from apps.organizations.models import (
    Division,
    Employee,
    Organization,
    Position,
)


def minimal_xlsx() -> bytes:
    content_types = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" '
        'ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.'
        'spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.'
        'spreadsheetml.worksheet+xml"/>'
        "</Types>"
    )
    relationships = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/'
        'officeDocument" Target="xl/workbook.xml"/>'
        "</Relationships>"
    )
    workbook = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets><sheet name="Лист1" sheetId="1" r:id="rId1"/></sheets>'
        "</workbook>"
    )
    workbook_relationships = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/'
        'worksheet" Target="worksheets/sheet1.xml"/>'
        "</Relationships>"
    )
    worksheet = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        "<sheetData>"
        '<row r="1">'
        '<c r="A1" t="inlineStr"><is><t>Код</t></is></c>'
        '<c r="B1" t="inlineStr"><is><t>Наименование</t></is></c>'
        "</row>"
        '<row r="2">'
        '<c r="A2" t="inlineStr"><is><t>EQ-1</t></is></c>'
        '<c r="B2"><f>1+1</f><v>2</v></c>'
        "</row>"
        "</sheetData>"
        "</worksheet>"
    )
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", relationships)
        archive.writestr("xl/workbook.xml", workbook)
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_relationships)
        archive.writestr("xl/worksheets/sheet1.xml", worksheet)
    return stream.getvalue()



class ImportServiceTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.organization = Organization.objects.create(code="ORG", name="Организация")
        division = Division.objects.create(
            organization=self.organization,
            code="DIV",
            name="Подразделение",
        )
        position = Position.objects.create(
            organization=self.organization,
            code="POS",
            name="Специалист",
        )
        self.user = user_model.objects.create_user(username="importer")
        self.employee = Employee.objects.create(
            organization=self.organization,
            division=division,
            position=position,
            user=self.user,
            personnel_number="EMP-1",
            last_name="Тестов",
            first_name="Импорт",
            employment_start=date(2026, 1, 1),
        )

    def upload(self, content: bytes, name: str = "data.csv"):
        return SimpleUploadedFile(name, content)

    def test_normalize_cell_preserves_meaning_and_collapses_spaces(self):
        self.assertEqual(normalize_cell("  КТП\u00a0  01  "), "КТП 01")

    def test_csv_semicolon_is_parsed_and_headers_are_recognized(self):
        batch = create_import_batch(
            uploaded_file=self.upload("Код;Наименование\nEQ-1; КТП  01\n".encode()),
            target_registry=ImportBatch.TargetRegistry.EQUIPMENT,
            employee=self.employee,
        )
        self.assertEqual(batch.status, ImportBatch.Status.READY)
        self.assertEqual(batch.source_delimiter, ";")
        row = batch.rows.get()
        self.assertEqual(row.status, ImportRow.Status.RECOGNIZED)
        self.assertEqual(row.source_values[1], " КТП  01")
        self.assertEqual(row.normalized_values[1], "КТП 01")

    def test_duplicates_and_empty_rows_receive_explicit_statuses(self):
        batch = create_import_batch(
            uploaded_file=self.upload(
                "Код;Наименование\nEQ-1;КТП\nEQ-1;КТП\n;\n".encode()
            ),
            target_registry=ImportBatch.TargetRegistry.EQUIPMENT,
            employee=self.employee,
        )
        statuses = list(batch.rows.values_list("status", flat=True))
        self.assertEqual(statuses.count(ImportRow.Status.CONFLICT), 2)
        self.assertEqual(statuses.count(ImportRow.Status.REJECTED), 1)

    def test_xlsx_formula_is_saved_as_text_and_requires_review(self):
        batch = create_import_batch(
            uploaded_file=self.upload(
                minimal_xlsx(),
                "formula.xlsx",
            ),
            target_registry=ImportBatch.TargetRegistry.OTHER,
            employee=self.employee,
        )
        self.assertEqual(batch.sheet_name, "Лист1")
        row = batch.rows.get()
        self.assertEqual(row.source_values[1], "=1+1")
        self.assertEqual(row.status, ImportRow.Status.REVIEW)
        self.assertIn("не выполнялась", " ".join(row.issues))

    def test_discard_retains_rows_and_adds_audit_event(self):
        batch = create_import_batch(
            uploaded_file=self.upload("Код;Наименование\nEQ-1;КТП\n".encode()),
            target_registry=ImportBatch.TargetRegistry.EQUIPMENT,
            employee=self.employee,
        )
        row_count = batch.rows.count()
        discard_import_batch(batch=batch, employee=self.employee)
        batch.refresh_from_db()
        self.assertEqual(batch.status, ImportBatch.Status.DISCARDED)
        self.assertEqual(batch.rows.count(), row_count)
        self.assertTrue(
            batch.events.filter(event_type=ImportEvent.EventType.DISCARDED).exists()
        )
