from __future__ import annotations

import io
import zipfile
from datetime import date

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.imports.models import ImportBatch, ImportRow
from apps.imports.services import (
    create_import_batch,
    parse_tabular_file,
    save_column_mapping,
)
from apps.organizations.models import (
    Division,
    Employee,
    Organization,
    Position,
)


def _xlsx_package(
    worksheet: str,
    *,
    styles: str = "",
    date_system_1904: bool = False,
) -> bytes:
    style_override = (
        '<Override PartName="/xl/styles.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.'
        'spreadsheetml.styles+xml"/>'
        if styles
        else ""
    )
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
        f"{style_override}"
        "</Types>"
    )
    root_relationships = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/'
        'officeDocument" Target="xl/workbook.xml"/>'
        "</Relationships>"
    )
    workbook_properties = (
        '<workbookPr date1904="1"/>'
        if date_system_1904
        else ""
    )
    workbook = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f"{workbook_properties}"
        '<sheets><sheet name="Сотрудники" sheetId="1" r:id="rId1"/></sheets>'
        "</workbook>"
    )
    style_relationship = (
        '<Relationship Id="rId2" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/'
        'styles" Target="styles.xml"/>'
        if styles
        else ""
    )
    workbook_relationships = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/'
        'worksheet" Target="worksheets/sheet1.xml"/>'
        f"{style_relationship}"
        "</Relationships>"
    )

    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", root_relationships)
        archive.writestr("xl/workbook.xml", workbook)
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_relationships)
        archive.writestr("xl/worksheets/sheet1.xml", worksheet)
        if styles:
            archive.writestr("xl/styles.xml", styles)
    return stream.getvalue()


def _styles(
    *,
    number_format_id: int,
    format_code: str | None = None,
    second_number_format_id: int | None = None,
) -> str:
    custom = (
        '<numFmts count="1">'
        f'<numFmt numFmtId="{number_format_id}" formatCode="{format_code.replace(chr(34), "&quot;")}"/>'
        "</numFmts>"
        if format_code is not None
        else ""
    )
    second = (
        f'<xf numFmtId="{second_number_format_id}"/>'
        if second_number_format_id is not None
        else ""
    )
    count = 2 + int(second_number_format_id is not None)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f"{custom}"
        f'<cellXfs count="{count}">'
        '<xf numFmtId="0"/>'
        f'<xf numFmtId="{number_format_id}"/>'
        f"{second}"
        "</cellXfs>"
        "</styleSheet>"
    )


def _single_row_sheet(
    *,
    value: str,
    style_index: int = 1,
    cell_type: str = "n",
    extra_cells: str = "",
) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        "<sheetData>"
        '<row r="1"><c r="A1" t="inlineStr"><is><t>Дата</t></is></c>'
        '<c r="B1" t="inlineStr"><is><t>Число</t></is></c>'
        '<c r="C1" t="inlineStr"><is><t>Логическое</t></is></c></row>'
        '<row r="2">'
        f'<c r="A2" s="{style_index}" t="{cell_type}"><v>{value}</v></c>'
        f"{extra_cells}"
        "</row>"
        "</sheetData>"
        "</worksheet>"
    )


class TypedXlsxCellTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.organization = Organization.objects.create(
            code="ORG-XLSX",
            name="Организация XLSX",
        )
        self.division = Division.objects.create(
            organization=self.organization,
            code="OPS",
            name="Участок оперативного обслуживания ВЭС",
        )
        self.position = Position.objects.create(
            organization=self.organization,
            code="ELECTRICIAN",
            name="Электромонтёр",
        )
        self.user = user_model.objects.create_user(username="xlsx-importer")
        self.employee = Employee.objects.create(
            organization=self.organization,
            division=self.division,
            position=self.position,
            user=self.user,
            personnel_number="EMP-XLSX",
            last_name="Тестов",
            first_name="Импорт",
            employment_start=date(2026, 1, 1),
        )

    def _upload(self, content: bytes, name: str = "typed.xlsx"):
        return SimpleUploadedFile(name, content)

    def test_custom_date_style_keeps_display_and_normalizes_iso(self):
        parsed = parse_tabular_file(
            _xlsx_package(
                _single_row_sheet(value="46220"),
                styles=_styles(
                    number_format_id=200,
                    format_code="DD.MM.YYYY",
                ),
            ),
            "custom-date.xlsx",
        )
        self.assertEqual(parsed.rows[1][0], "17.07.2026")
        self.assertEqual(parsed.normalized_cells[(2, 0)], "2026-07-17")

    def test_builtin_date_style_is_recognized(self):
        parsed = parse_tabular_file(
            _xlsx_package(
                _single_row_sheet(value="46220"),
                styles=_styles(number_format_id=14),
            ),
            "builtin-date.xlsx",
        )
        self.assertEqual(parsed.rows[1][0], "17.07.2026")
        self.assertEqual(parsed.normalized_cells[(2, 0)], "2026-07-17")

    def test_1904_date_system_is_supported(self):
        serial = (date(2026, 7, 17) - date(1904, 1, 1)).days
        parsed = parse_tabular_file(
            _xlsx_package(
                _single_row_sheet(value=str(serial)),
                styles=_styles(
                    number_format_id=200,
                    format_code="dd.mm.yyyy",
                ),
                date_system_1904=True,
            ),
            "date-1904.xlsx",
        )
        self.assertEqual(parsed.rows[1][0], "17.07.2026")
        self.assertEqual(parsed.normalized_cells[(2, 0)], "2026-07-17")

    def test_general_numeric_serial_is_not_treated_as_date(self):
        parsed = parse_tabular_file(
            _xlsx_package(
                _single_row_sheet(value="46220", style_index=0),
            ),
            "ordinary-number.xlsx",
        )
        self.assertEqual(parsed.rows[1][0], "46220")
        self.assertNotIn((2, 0), parsed.normalized_cells)

    def test_quoted_date_letters_do_not_turn_number_into_date(self):
        parsed = parse_tabular_file(
            _xlsx_package(
                _single_row_sheet(value="46220"),
                styles=_styles(
                    number_format_id=200,
                    format_code='0 "days"',
                ),
            ),
            "quoted-text-format.xlsx",
        )
        self.assertEqual(parsed.rows[1][0], "46220")
        self.assertNotIn((2, 0), parsed.normalized_cells)

    def test_datetime_and_boolean_cells_are_normalized(self):
        parsed = parse_tabular_file(
            _xlsx_package(
                _single_row_sheet(
                    value="46220.5",
                    extra_cells=(
                        '<c r="B2"><v>46220</v></c>'
                        '<c r="C2" t="b"><v>1</v></c>'
                    ),
                ),
                styles=_styles(number_format_id=22),
            ),
            "datetime-and-boolean.xlsx",
        )
        self.assertEqual(parsed.rows[1][0], "17.07.2026 12:00:00")
        self.assertEqual(parsed.normalized_cells[(2, 0)], "2026-07-17T12:00:00")
        self.assertEqual(parsed.rows[1][1], "46220")
        self.assertEqual(parsed.rows[1][2], "ИСТИНА")
        self.assertEqual(parsed.normalized_cells[(2, 2)], "Да")

    def test_excel_fake_leap_day_is_not_silently_converted(self):
        parsed = parse_tabular_file(
            _xlsx_package(
                _single_row_sheet(value="60"),
                styles=_styles(number_format_id=14),
            ),
            "excel-fake-leap-day.xlsx",
        )
        self.assertEqual(parsed.rows[1][0], "60")
        self.assertNotIn((2, 0), parsed.normalized_cells)

    def test_personnel_date_passes_mapping_without_manual_correction(self):
        headers = (
            "Табельный номер",
            "Фамилия",
            "Имя",
            "Отчество",
            "Подразделение",
            "Должность",
            "Дата начала работы",
            "Действующий сотрудник",
        )
        header_cells = "".join(
            f'<c r="{chr(65 + index)}1" t="inlineStr"><is><t>{label}</t></is></c>'
            for index, label in enumerate(headers)
        )
        values = (
            "DEMO-201",
            "Иванов",
            "Максим",
            "Алексеевич",
            self.division.name,
            self.position.name,
        )
        value_cells = "".join(
            f'<c r="{chr(65 + index)}2" t="inlineStr"><is><t>{value}</t></is></c>'
            for index, value in enumerate(values)
        )
        worksheet = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            "<sheetData>"
            f'<row r="1">{header_cells}</row>'
            f'<row r="2">{value_cells}'
            '<c r="G2" s="1" t="n"><v>46220</v></c>'
            '<c r="H2" t="inlineStr"><is><t>Да</t></is></c>'
            "</row>"
            "</sheetData>"
            "</worksheet>"
        )
        batch = create_import_batch(
            uploaded_file=self._upload(
                _xlsx_package(
                    worksheet,
                    styles=_styles(
                        number_format_id=200,
                        format_code="DD.MM.YYYY",
                    ),
                ),
                "employees.xlsx",
            ),
            target_registry=ImportBatch.TargetRegistry.ORGANIZATION,
            employee=self.employee,
        )
        mapping = {
            column.position: column.mapped_key
            for column in batch.columns.order_by("position")
        }
        save_column_mapping(
            batch=batch,
            employee=self.employee,
            mapping=mapping,
        )
        row = batch.rows.get()
        self.assertEqual(row.source_values[6], "17.07.2026")
        self.assertEqual(row.normalized_values[6], "2026-07-17")
        self.assertEqual(row.mapped_values["employment_start"], "2026-07-17")
        self.assertEqual(row.validation_issues, [])
        self.assertEqual(row.review_status, ImportRow.ReviewStatus.VALID)
