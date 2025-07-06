import pytest
from bims.prism.models import Blueprint, LoadProfile, Zone, Project
from bims.prism.eval import MiniEvalEngine


@pytest.mark.unit
def test_cross_team_override():
    bp1 = Blueprint.parse_file("tests/fixtures/depblueprint.yaml")   # team: demo
    bp2 = Blueprint.parse_file("tests/fixtures/altblueprint.yaml")   # team: alt-team

    load = LoadProfile.parse_file("tests/fixtures/miniload.yaml")
    zone = Zone(name="default", enabled_modules=["inspection"], load_profile=load)
    project = Project(customer="override-test", zones=[zone])

    res = MiniEvalEngine([bp1, bp2], project).run()

    assert res.warnings is not None
    ovrs = res.warnings.overrides
    assert any(o.name == "notification" and o.kind == "generic_service" for o in ovrs)
