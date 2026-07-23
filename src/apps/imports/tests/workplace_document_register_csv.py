from __future__ import annotations

import csv
import io

from apps.imports.workplace_documents import WORKPLACE_DOCUMENT_HEADER


def synthetic_workplace_document_rows() -> list[dict[str, str]]:
    return [
        {
            "index": "0",
            "register_entry_no": "1",
            "section_no": "1",
            "section_name": "Пожарная безопасность",
            "subsection_no": "",
            "subsection_name": "",
            "source_document_no": "1",
            "document_title_raw": "Перечень безопасного отключения электроустановок",
            "document_type_proposed": "Перечень",
            "electronic_storage_mark": "+",
            "electronic_storage_interpretation": "INDICATED",
            "review_period_raw": "1 раз в 3 года",
            "review_interval_years_proposed": "3.0",
            "approval_date_from_title_page": "2024-08-07",
            "approving_role_from_title_page": "Технический директор",
            "approver_from_title_page": "И.А. Тестов",
            "workplace_scope": "Рабочее место оперативного персонала Кочубеевской ВЭС",
            "source_pdf_page": "2",
            "source_notes": "",
        },
        {
            "index": "1",
            "register_entry_no": "2",
            "section_no": "1",
            "section_name": "Пожарная безопасность",
            "subsection_no": "",
            "subsection_name": "",
            "source_document_no": "2",
            "document_title_raw": "Инструкция действий оперативного персонала",
            "document_type_proposed": "Инструкция",
            "electronic_storage_mark": "-",
            "electronic_storage_interpretation": "NOT_INDICATED",
            "review_period_raw": "-",
            "review_interval_years_proposed": "",
            "approval_date_from_title_page": "2024-08-07",
            "approving_role_from_title_page": "Технический директор",
            "approver_from_title_page": "И.А. Тестов",
            "workplace_scope": "Рабочее место оперативного персонала Кочубеевской ВЭС",
            "source_pdf_page": "2",
            "source_notes": "",
        },
    ]


def synthetic_workplace_document_csv(
    *,
    rows: list[dict[str, str]] | None = None,
    bom: bool = True,
) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=WORKPLACE_DOCUMENT_HEADER, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows or synthetic_workplace_document_rows())
    payload = buffer.getvalue().encode("utf-8")
    return b"\xef\xbb\xbf" + payload if bom else payload
