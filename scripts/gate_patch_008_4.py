from __future__ import annotations

import io
import os
import sys
import zipfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("DB_ENGINE", "sqlite")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eod_config.settings")
os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

import django  # noqa: E402

django.setup()

from apps.imports.services import parse_tabular_file  # noqa: E402


def xlsx(
    *,
    serial: str,
    number_format_id: int = 200,
    format_code: str | None = "DD.MM.YYYY",
    date_system_1904: bool = False,
    style_index: int = 1,
    boolean: bool = False,
) -> bytes:
    escaped_code = (
        format_code.replace('"', "&quot;")
        if format_code is not None
        else None
    )
    num_fmts = (
        '<numFmts count="1">'
        f'<numFmt numFmtId="{number_format_id}" formatCode="{escaped_code}"/>'
        "</numFmts>"
        if escaped_code is not None
        else ""
    )
    styles = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f"{num_fmts}"
        '<cellXfs count="2">'
        '<xf numFmtId="0"/>'
        f'<xf numFmtId="{number_format_id}"/>'
        "</cellXfs>"
        "</styleSheet>"
    )
    workbook_properties = (
        '<workbookPr date1904="1"/>'
        if date_system_1904
        else ""
    )
    bool_cell = '<c r="C2" t="b"><v>1</v></c>' if boolean else ""
    worksheet = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        "<sheetData>"
        '<row r="1">'
        '<c r="A1" t="inlineStr"><is><t>Дата</t></is></c>'
        '<c r="B1" t="inlineStr"><is><t>Число</t></is></c>'
        '<c r="C1" t="inlineStr"><is><t>Логическое</t></is></c>'
        "</row>"
        '<row r="2">'
        f'<c r="A2" s="{style_index}" t="n"><v>{serial}</v></c>'
        f'<c r="B2" t="n"><v>{serial}</v></c>'
        f"{bool_cell}"
        "</row>"
        "</sheetData>"
        "</worksheet>"
    )
    workbook = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f"{workbook_properties}"
        '<sheets><sheet name="Проверка" sheetId="1" r:id="rId1"/></sheets>'
        "</workbook>"
    )
    workbook_relationships = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/'
        'worksheet" Target="worksheets/sheet1.xml"/>'
        '<Relationship Id="rId2" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/'
        'styles" Target="styles.xml"/>'
        "</Relationships>"
    )
    root_relationships = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/'
        'officeDocument" Target="xl/workbook.xml"/>'
        "</Relationships>"
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
        '<Override PartName="/xl/styles.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.'
        'spreadsheetml.styles+xml"/>'
        "</Types>"
    )

    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", root_relationships)
        archive.writestr("xl/workbook.xml", workbook)
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_relationships)
        archive.writestr("xl/worksheets/sheet1.xml", worksheet)
        archive.writestr("xl/styles.xml", styles)
    return stream.getvalue()


custom = parse_tabular_file(xlsx(serial="46220", boolean=True), "custom.xlsx")
if custom.rows[1][0] != "17.07.2026":
    raise SystemExit(f"Custom date display mismatch: {custom.rows[1][0]!r}")
if custom.normalized_cells.get((2, 0)) != "2026-07-17":
    raise SystemExit("Custom date normalization mismatch.")
if custom.rows[1][1] != "46220" or (2, 1) in custom.normalized_cells:
    raise SystemExit("Ordinary numeric cell was incorrectly converted to a date.")
if custom.rows[1][2] != "ИСТИНА" or custom.normalized_cells.get((2, 2)) != "Да":
    raise SystemExit("Boolean XLSX cell normalization mismatch.")
print("XLSX_CUSTOM_DATE_STYLE=PASSED")
print("XLSX_SOURCE_AND_NORMALIZED_VALUES=PASSED")
print("XLSX_NON_DATE_NUMERIC_SAFETY=PASSED")
print("XLSX_BOOLEAN_CELL=PASSED")

serial_1904 = str((date(2026, 7, 17) - date(1904, 1, 1)).days)
workbook_1904 = parse_tabular_file(
    xlsx(serial=serial_1904, date_system_1904=True),
    "date-1904.xlsx",
)
if workbook_1904.normalized_cells.get((2, 0)) != "2026-07-17":
    raise SystemExit("1904 date system normalization mismatch.")
print("XLSX_1900_AND_1904_DATE_SYSTEMS=PASSED")

quoted = parse_tabular_file(
    xlsx(serial="46220", format_code='0 "days"'),
    "quoted-format.xlsx",
)
if quoted.rows[1][0] != "46220" or (2, 0) in quoted.normalized_cells:
    raise SystemExit("Quoted text in number format caused false date detection.")
print("XLSX_FORMAT_FALSE_POSITIVE_PROTECTION=PASSED")
print("PATCH_008_4_TYPED_XLSX_CELLS_GATE_PASSED")
