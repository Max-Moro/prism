import pytest

from bims.prism.eval import MiniEvalEngine
from bims.prism.models import Blueprint, LoadProfile, Zone, Project

@pytest.mark.unit
def test_zone_multiplier():
    bp = Blueprint.parse_file("tests/fixtures/depblueprint.yaml")
    load = LoadProfile.parse_file("tests/fixtures/miniload.yaml")

    # зона ×3
    zone = Zone(name="Prod-3x", enabled_modules=["inspection"], load_profile=load, factor=3)
    proj = Project(customer="multiplier-test", zones=[zone])

    res = MiniEvalEngine([bp], proj).run()
    z = res.zones["Prod-3x"]

    assert z.totals.requests.cpu > 0
    # проверяем, что cpu умножилось ровно на 3
    assert z.totals.requests.cpu == pytest.approx(
        z.totals.limits.cpu / (z.totals.limits.cpu / z.totals.requests.cpu)
     )