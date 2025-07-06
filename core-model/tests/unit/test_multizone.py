import pytest
from bims.prism.eval import MiniEvalEngine
from bims.prism.models import Project, Blueprint


@pytest.mark.unit
def test_multizone():
    project = Project.parse_file("tests/fixtures/project.yaml")
    bp      = Blueprint.parse_file("tests/fixtures/depblueprint.yaml")

    res = MiniEvalEngine([bp], project).run().details

    assert "Prod" in res["zones"] and "Test" in res["zones"]
    assert res["totals"]["requests"]["cpu"] > res["zones"]["Test"]["totals"]["requests"]["cpu"]

    # aggregated infra sizing
    pg_total = (
        res["zones"]["Prod"]["infra"]["postgres-primary"]["capacity"]["storage_gb"]
        + res["zones"]["Test"]["infra"]["postgres-primary"]["capacity"]["storage_gb"]
    )
    assert res["infra_totals"]["postgres"]["storage_gb"] == pytest.approx(pg_total)
