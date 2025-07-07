from __future__ import annotations

import io
import re
import zipfile
from typing import Final, Dict

_EPOCH: Final = (1980, 1, 1, 0, 0, 0)          # фикс-timestamp
_CORE_REPL: Final[Dict[bytes, bytes]] = {
    # заменяем ISO-дату внутри dcterms тегов на epoch-дату
    br"<dcterms:created>[^<]+</dcterms:created>":
    b"<dcterms:created>1980-01-01T00:00:00Z</dcterms:created>",
    br"<dcterms:modified>[^<]+</dcterms:modified>":
    b"<dcterms:modified>1980-01-01T00:00:00Z</dcterms:modified>",
}

_APP_REPL: Final[Dict[bytes, bytes]] = {
    br"<TotalTime>[^<]+</TotalTime>":
    b"<TotalTime>0</TotalTime>",
}

def _canonicalize_core_xml(src: bytes) -> bytes:
    """Заменяет только плавающие timestamps."""
    for pattern, repl in _CORE_REPL.items():
        src = re.sub(pattern, repl, src)
    return src

def _canonicalize_app_xml(src: bytes) -> bytes:
    for pattern, repl in _APP_REPL.items():
        src = re.sub(pattern, repl, src)
    return src

def normalize_xlsx(raw: bytes) -> bytes:
    """
    Возвращает копию XLSX с:
      • фиксированными ZipInfo.date_time
      • константными <dcterms:created/modified> в docProps/core.xml
    """
    src = io.BytesIO(raw)
    dst = io.BytesIO()

    with zipfile.ZipFile(src, "r") as zin, zipfile.ZipFile(
        dst, "w", compression=zipfile.ZIP_DEFLATED
    ) as zout:
        for zinfo in zin.infolist():
            data = zin.read(zinfo.filename)

            # ── canonicalize metadata ───────────────────────
            if zinfo.filename == "docProps/core.xml":
                data = _canonicalize_core_xml(data)
            elif zinfo.filename == "docProps/app.xml":
                data = _canonicalize_app_xml(data)

            zi = zipfile.ZipInfo(zinfo.filename, date_time=_EPOCH)
            zi.external_attr = zinfo.external_attr
            zi.compress_type = zipfile.ZIP_DEFLATED
            zout.writestr(zi, data)

    return dst.getvalue()
