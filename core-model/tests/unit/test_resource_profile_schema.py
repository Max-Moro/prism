import pytest
import yaml
from pathlib import Path

from bims.prism.models import Blueprint


@pytest.mark.unit
def test_valid_profiles(tmp_path):
    """Любой существующий фикстурный Blueprint должен валидироваться."""
    Blueprint.parse_file("tests/fixtures/miniblueprint.yaml")
    Blueprint.parse_file("tests/fixtures/depblueprint.yaml")


@pytest.mark.unit
def test_invalid_profile(tmp_path):
    """Пропускаем поле `cpu` — ожидание падения на JSON-Schema."""
    bad = yaml.safe_load(Path("tests/fixtures/miniblueprint.yaml").read_text())
    bad["resource_profiles"]["xsmall-web"]["static"]["requests"].pop("cpu")

    bp = tmp_path / "bad.yaml"
    bp.write_text(yaml.dump(bad), encoding="utf-8")

    with pytest.raises(ValueError, match="ResourceProfile 'xsmall-web' invalid"):
        Blueprint.parse_file(bp)