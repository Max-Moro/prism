import pytest
import yaml

from bims.prism.models import LoadProfile

@pytest.mark.unit
def test_load_profile_schema_ok(tmp_path):
    sample = {
        "online_users": 500,
        "total_users": 2000,
        "rps": 120,
        "rps_p95": 100,
        "jobs_rate": 20,
        "structured_data_gb": 50,
        "unstructured_data_gb": 300
    }
    f = tmp_path / "load.yaml"
    f.write_text(yaml.dump(sample), encoding="utf-8")

    lp = LoadProfile.parse_file(f)
    assert lp.online_users == 500

@pytest.mark.unit
def test_load_profile_schema_typo(tmp_path):
    bad = { "onlne_users": 10 }  # typo!
    f = tmp_path / "bad.yaml"
    f.write_text(yaml.dump(bad), encoding="utf-8")

    with pytest.raises(ValueError, match="JSON-Schema"):
        LoadProfile.parse_file(f)
