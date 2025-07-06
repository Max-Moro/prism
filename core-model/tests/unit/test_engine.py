import json
import math
from pathlib import Path

import pytest

from bims.prism.eval import MiniEvalEngine
from bims.prism.models import Blueprint, LoadProfile, Project, Zone


@pytest.mark.unit
def test_engine_minimal(tmp_path):
    """
    Мини-проект: 1 Blueprint + 1 Zone без enabled_modules.
    Берём *все* technical-services.
    """
    bp = Blueprint.parse_file("tests/fixtures/miniblueprint.yaml")
    load = LoadProfile.parse_file("tests/fixtures/miniload.yaml")

    # обходим валидацию min_length=1 — этого достаточно для юнит-теста
    zone = Zone.model_construct(name="default", enabled_modules=[], load_profile=load)
    project = Project.model_construct(customer="unit-test", zones=[zone])

    got = MiniEvalEngine([bp], project).run()
    zone_res = got.zones["default"]

    want = json.loads(Path("tests/fixtures/expected.json").read_text())

    assert math.isclose(
        zone_res.totals.requests.cpu, want["totals"]["requests"]["cpu"]
    )
    assert zone_res.services["worker"].limits.cpu_cores == 0.3


@pytest.mark.unit
def test_dep_graph():
    """
    Граф: technical → generic → infra, корневой BusinessModule = inspection.
    """
    bp = Blueprint.parse_file("tests/fixtures/depblueprint.yaml")
    load = LoadProfile.parse_file("tests/fixtures/miniload.yaml")

    zone = Zone(name="default", enabled_modules=["inspection"], load_profile=load)
    project = Project(customer="unit-test", zones=[zone])

    res = MiniEvalEngine([bp], project).run()
    zone_res = res.zones["default"]

    assert "notification" in zone_res.generic_services
    assert "postgres-primary" in zone_res.infra
    assert math.isclose(
        zone_res.infra["postgres-primary"].capacity["storage_gb"], 11.9
    )
