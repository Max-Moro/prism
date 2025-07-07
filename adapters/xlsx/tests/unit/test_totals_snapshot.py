import json
from pathlib import Path
from typing import List, Any
import io

import openpyxl
import pytest

from bims.prism.adapters.xlsx import build_report


def _sheet_to_matrix(xlsx_bytes: bytes) -> List[List[Any]]:
    wb = openpyxl.load_workbook(
        io.BytesIO(xlsx_bytes),      # ← передаём как файл-объект
        data_only=True,
        read_only=True,
    )
    ws = wb["Totals"]
    return [list(row) for row in ws.iter_rows(values_only=True)]


@pytest.mark.unit
def test_totals_values():
    sizing = json.loads(Path("tests/fixtures/sample_sizing.json").read_text())
    matrix = _sheet_to_matrix(build_report(sizing))

    expected = [
        ["Zone", "CPU req (cores)", "Memory req", "CPU lim", "Memory lim"],
        ["Prod", 8.25, "32Gi", 12.0, "64Gi"],
        ["Test", 1.5, "8Gi", 2.5, "16Gi"],
    ]

    assert matrix == expected
