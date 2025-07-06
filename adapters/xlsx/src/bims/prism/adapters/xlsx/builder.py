"""XlsxAdapter — версия 0.1-skeleton: создаёт книгу с единственной ячейкой."""

from __future__ import annotations
from io import BytesIO

import openpyxl


class XlsxAdapter:
    def __init__(self, *, theme: str = "default") -> None:
        self.theme = theme

    def build(self, sizing_result):  # noqa: ANN001
        # sizing_result пока игнорируем, важно вернуть валидный файл
        wb = openpyxl.Workbook()
        sheet = wb.active
        sheet.title = "PRISM"
        sheet["A1"] = "Hello PRISM — XLSX skeleton ☑"
        buf = BytesIO()
        wb.save(buf)
        return buf.getvalue()
