import pytest

import json
import math
from pathlib import Path

from bims.prism.eval import MiniEvalEngine
from bims.prism.models import Blueprint, LoadProfile

@pytest.mark.unit
def test_engine_minimal(tmp_path):
    bp = Blueprint.parse_file("tests/fixtures/miniblueprint.yaml")
    load = LoadProfile.parse_file("tests/fixtures/miniload.yaml")
    engine = MiniEvalEngine([bp], load)

    got = engine.run().details
    want = json.loads(Path("tests/fixtures/expected.json").read_text())

    # глубокое равенство с tol для float
    assert math.isclose(got["totals"]["requests"]["cpu"],
                        want["totals"]["requests"]["cpu"])
    assert got["services"]["worker"]["limits"]["cpu_cores"] == 0.3
