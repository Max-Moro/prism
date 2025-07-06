"""
Расширенный конвертер единиц:
  * CPU: cores, `m`
  * Memory: Ki / Mi / Gi / Ti  (двоичные)  и  KB / MB / GB / TB (десятичные)
  * IOPS: `NNN/s` или `NNNiops` — считываются как «как есть»

Обратная функция `format_bytes()` используется генераторами отчётов
для человекочитаемого вывода.
"""

from __future__ import annotations

import re
from typing import Final

# ---------------------------------------------------------------- regex / map
_RE = re.compile(
    r"""^(?P<num>\d+(?:\.\d+)?)
        (?P<unit>
            (?:[KMGT]i?|[KMG]B|TB|m|/s|iops)?
        )$""",
    re.IGNORECASE | re.VERBOSE,
)

_MULTIPLIER: Final[dict[str, float]] = {
    # «как есть»
    "": 1,
    # CPU
    "m": 0.001,
    # IEC-бинарные
    "Ki": 1024**1,
    "Mi": 1024**2,
    "Gi": 1024**3,
    "Ti": 1024**4,
    # decimal-SI
    "KB": 1000**1,
    "MB": 1000**2,
    "GB": 1000**3,
    "TB": 1000**4,
    # IOPS
    "/s": 1,
    "iops": 1,
}

# поддерживаем строчные варианты ключей
_MULTIPLIER.update({k.lower(): v for k, v in _MULTIPLIER.items()})

def parse_quantity(raw: str) -> float:
    """
    >>> parse_quantity("150m")      # CPU → cores
    0.15
    >>> parse_quantity("512Mi")
    536870912
    >>> parse_quantity("1Ti")
    1099511627776
    >>> parse_quantity("256MB")
    256000000.0
    >>> parse_quantity("1500/s")    # IOPS
    1500.0
    """
    m = _RE.match(raw.strip())
    if not m:                   # noqa: WPS504
        raise ValueError(f"Bad quantity: {raw}")
    num  = float(m.group("num"))
    unit = m.group("unit") or ""
    try:
        return num * _MULTIPLIER[unit]
    except KeyError as exc:  # pragma: no cover
        raise ValueError(f"Unsupported unit: {unit}") from exc


# ─────────────────────────────────────────────────────────────────────────────
# Human-friendly рендер для bytes → Mi | Gi | Ti
# ─────────────────────────────────────────────────────────────────────────────

_BYTE_UNITS = [
    ("Ti", 1024**4),
    ("Gi", 1024**3),
    ("Mi", 1024**2),
    ("Ki", 1024**1),
]


def format_bytes(value: float | int, *, precision: int = 2) -> str:
    """
    >>> format_bytes(536870912)
    '512.00Mi'
    >>> format_bytes(30 * 1024**3)
    '30.00Gi'
    """
    if value < 1:
        return f"{value}B"

    for suffix, factor in _BYTE_UNITS:
        if value >= factor:
            return f"{value / factor:.{precision}f}{suffix}"

    # меньше Ki — покажем «NN B»
    return f"{value}B"
