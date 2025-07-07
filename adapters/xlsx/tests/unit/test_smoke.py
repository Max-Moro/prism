from pathlib import Path
import json

import pytest
from bims.prism.adapters.xlsx import build_report


@pytest.mark.unit
def test_skeleton_build(tmp_path):
    # минимальный SizingResult-like словарь
    fixture = Path("tests/fixtures/sample_sizing.json")

    sizing = json.loads(fixture.read_text(encoding="utf-8"))

    data = build_report(sizing)  # dummy arg

    outfile = tmp_path / "skeleton.xlsx"
    outfile.write_bytes(data)

    assert data[:2] == b"PK"      # XLSX = ZIP archive
    assert len(data) > 200        # не пустой
