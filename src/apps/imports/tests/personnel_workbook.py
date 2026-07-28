from __future__ import annotations

import io
import zipfile
from xml.sax.saxutils import escape


_SYNTHETIC_PERSONNEL_WORKBOOK: bytes | None = None


def _column_number(column: str) -> int:
    result = 0
    for character in column:
        result = result * 26 + ord(character) - ord("A") + 1
    return result


def synthetic_personnel_workbook() -> bytes:
    global _SYNTHETIC_PERSONNEL_WORKBOOK
    if _SYNTHETIC_PERSONNEL_WORKBOOK is not None:
        return _SYNTHETIC_PERSONNEL_WORKBOOK

    cells: dict[str, str] = {
        "Y4": "от 22.07.2026",
        "Z4": "№ TEST-0116",
        "A7": "№ п/п",
        "B7": "Фамилия, имя, отчество",
        "C7": "Должность",
        "D7": "Структурное подразделение",
        "E7": "Категория персонала",
        "F7": "Группа по электробезопасности, класс напряжения",
        "G7": "Диспетчерская заявка",
        "I7": "Оперативная заявка",
        "K7": "Выдача разрешения на деблокирование при неисправной блокировке",
        "L7": "Выдача разрешения на подготовку рабочего места и допуск",
        "M7": "Выдача наряда-допуска, распоряжения",
        "N7": "Ответственный руководитель работ",
        "O7": "Допускающий",
        "P7": "Производитель работ",
        "Q7": "Наблюдающий",
        "R7": "Член бригады",
        "S7": "Единоличный осмотр",
        "T7": "Ведение оперативных переговоров",
        "U7": "Производство переключений",
        "V7": "Контроль переключений",
        "W7": "Электроустановка (ЭУ)",
        "X7": "Специальные работы",
        "AB7": "Категория допуска к работе по техническому обслуживанию устройств РЗА",
        "G8": "Подача",
        "H8": "Согласование",
        "I8": "Подача",
        "J8": "Согласование",
        "X8": "Работы на высоте",
        "Y8": "Работы под напряжением",
        "Z8": "Работы под наведённым напряжением",
        "AA8": "Испытания повышенным напряжением",
        "A9": "1",
        "B9": "Иванов Иван Иванович",
        "C9": "Начальник смены",
        "D9": "Оперативная служба",
        "E9": "ОП",
        "F9": "V до и выше 1000 В",
        "G9": "+",
        "H9": "–",
        "I9": "+2",
        "J9": "+3",
        "K9": "+",
        "L9": "+",
        "M9": "+ (ЭТО)",
        "N9": "+",
        "O9": "+",
        "P9": "+",
        "Q9": "–",
        "R9": "+",
        "S9": "+",
        "T9": "+",
        "U9": "+ (2 группа)",
        "V9": "+",
        "W9": "ЭУ до и выше 1000 В",
        "X9": "+ (3 группа)",
        "Y9": "+ (И2)",
        "Z9": "–",
        "AA9": "+",
        "AB9": "2",
        "A10": "2",
        "B10": "Петров Пётр Петрович",
        "C10": "Инженер",
        "D10": "Служба РЗА",
        "E10": "АТП",
        "F10": "IV до и выше 1000 В",
        "G10": "+",
        "H10": "–",
        "I10": "–",
        "J10": "–",
        "K10": "–",
        "L10": "–",
        "M10": "–",
        "N10": "+",
        "O10": "–",
        "P10": "+",
        "Q10": "+",
        "R10": "+",
        "S10": "+",
        "T10": "–",
        "U10": "–",
        "V10": "–",
        "W10": "ЭУ до и выше 1000 В",
        "X10": "–",
        "Y10": "+ (И2)",
        "Z10": "–",
        "AA10": "–",
        "AB10": "–",
        "B85": '"+" – право предоставлено',
        "B86": '"–" – право не предоставлено',
        "B87": "1 – синтетическая сноска 1",
        "B88": "2 – синтетическая сноска 2",
    }
    rows: dict[int, list[tuple[str, str]]] = {}
    for reference, value in cells.items():
        row_number = int("".join(character for character in reference if character.isdigit()))
        rows.setdefault(row_number, []).append((reference, value))
    row_xml: list[str] = []
    for row_number in sorted(rows):
        entries = sorted(
            rows[row_number],
            key=lambda item: _column_number("".join(c for c in item[0] if c.isalpha())),
        )
        cell_xml = "".join(
            f'<c r="{reference}" t="inlineStr"><is><t>{escape(value)}</t></is></c>'
            for reference, value in entries
        )
        row_xml.append(f'<row r="{row_number}">{cell_xml}</row>')

    worksheet = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{"".join(row_xml)}</sheetData></worksheet>'
    )
    workbook = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets><sheet name="Приложение" sheetId="1" r:id="rId1"/></sheets></workbook>'
    )
    relationships = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
        'Target="worksheets/sheet1.xml"/></Relationships>'
    )
    root_relationships = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="xl/workbook.xml"/></Relationships>'
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        '</Types>'
    )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", root_relationships)
        archive.writestr("xl/workbook.xml", workbook)
        archive.writestr("xl/_rels/workbook.xml.rels", relationships)
        archive.writestr("xl/worksheets/sheet1.xml", worksheet)
    _SYNTHETIC_PERSONNEL_WORKBOOK = buffer.getvalue()
    return _SYNTHETIC_PERSONNEL_WORKBOOK
