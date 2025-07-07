import math

import pytest

from bims.prism.common.units import format_bytes, parse_quantity


@pytest.mark.unit
def test_parse_new_units():
    assert parse_quantity("1Gi") == 1024**3
    assert parse_quantity("2Ti") == 2 * 1024**4
    assert parse_quantity("256MB") == 256 * 1_000_000
    assert parse_quantity("1500/s") == 1500


@pytest.mark.unit
def test_format_bytes():
    assert format_bytes(512 * 1024**2) == "512.00Mi"
    assert format_bytes(3 * 1024**3) == "3.00Gi"
    # округление
    val = 1.5 * 1024**4
    assert math.isclose(parse_quantity(format_bytes(val)), val, rel_tol=1e-6)