from __future__ import annotations

from pathlib import Path

from django import forms

from .models import ImportBatch
from .services import MAX_FILE_SIZE


class ImportUploadForm(forms.Form):
    target_registry = forms.ChoiceField(
        label="Назначение импорта",
        choices=ImportBatch.TargetRegistry.choices,
    )
    source_file = forms.FileField(
        label="Файл",
        help_text="Поддерживаются CSV и XLSX размером до 10 МБ.",
        widget=forms.ClearableFileInput(attrs={"accept": ".csv,.xlsx"}),
    )

    def clean_source_file(self):
        uploaded = self.cleaned_data["source_file"]
        extension = Path(uploaded.name).suffix.lower()
        if extension not in {".csv", ".xlsx"}:
            raise forms.ValidationError("Допустимы только файлы CSV и XLSX.")
        if uploaded.size > MAX_FILE_SIZE:
            raise forms.ValidationError("Размер файла превышает 10 МБ.")
        if uploaded.size == 0:
            raise forms.ValidationError("Нельзя загрузить пустой файл.")
        return uploaded
