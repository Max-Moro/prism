import json
import math
from pathlib import Path

from bims.prism.eval import MiniEvalEngine
from bims.prism.models import Blueprint, LoadProfile


def test_engine_minimal(tmp_path):
    bp = Blueprint.parse_file("tests/fixtures/miniblueprint.yaml")
    load = LoadProfile.parse_file("tests/fixtures/miniload.yaml")
    engine = MiniEvalEngine([bp], load)

    got = engine.run().details
    want = json.loads(Path("tests/fixtures/expected.json").read_text())

    assert math.isclose(got["totals"]["cpu"], want["totals"]["cpu"])
    assert math.isclose(got["totals"]["memory"], want["totals"]["memory"])
    assert math.isclose(
        got["services"]["api"]["memory_bytes"],
        want["services"]["api"]["memory_bytes"],
    )
