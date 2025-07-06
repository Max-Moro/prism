# core-model/src/bims/prism/units.py
import re
from typing import Final

_RE = re.compile(r"^(?P<num>\d+(?:\.\d+)?)(?P<unit>[KMG]i?|m)?$", re.IGNORECASE)

_MULTIPLIER: Final = {
    "":   1,            # без суффикса – «как есть»
    "m":  0.001,        # millicore → cores
    "Ki": 1024**1,
    "Mi": 1024**2,
    "Gi": 1024**3,
    # поддержим строчные варианты
    "ki": 1024**1,
    "mi": 1024**2,
    "gi": 1024**3,
}

def parse_quantity(raw: str) -> float:
    """
    >>> parse_quantity("150m")      # CPU → cores
    0.15
    >>> parse_quantity("512Mi")     # Mem → bytes
    536870912
    """
    m = _RE.match(raw.strip())
    if not m:                   # noqa: WPS504
        raise ValueError(f"Bad quantity: {raw}")
    num  = float(m.group("num"))
    unit = m.group("unit") or ""
    return num * _MULTIPLIER[unit]
