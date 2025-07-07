"""
Typed SizingResult: обёртка над автоген-моделью с дополнительной JSON-Schema
валидацией (как у остальных моделей).
"""
from __future__ import annotations

import json
from importlib import resources
from pathlib import Path
from typing import Any, Dict

from jsonschema import validate as _js_validate, ValidationError as _JSValidationError
from pydantic import ValidationError as _PydValidationError

from ._gen.sizing_result_gen import PrismSizingResult as _SRGen

# Схема лежит в общем модуле в `prism-common` в bims.prism.common.schemas/sizing_result.schema.json
_SCHEMA = json.loads(
    resources.files("bims.prism.common.schemas")
    .joinpath("sizing_result.schema.json")
    .read_text(encoding="utf-8")
)


class SizingResult(_SRGen):  # type: ignore[misc]
    """Публичная модель вычисленного сайзинга."""

    # ---------------------------------------------------------------- helpers
    @classmethod
    def _validate_schema(cls, data: Dict[str, Any]) -> None:
        _js_validate(instance=data, schema=_SCHEMA)

    # ---------------------------------------------------------------- public
    @classmethod
    def parse_obj(cls, obj: Dict[str, Any]) -> "SizingResult":  # noqa: D401
        try:
            cls._validate_schema(obj)
        except _JSValidationError as exc:
            raise ValueError(f"SizingResult schema error: {exc.message}") from exc
        try:
            return cls.model_validate(obj)
        except _PydValidationError as exc:  # pragma: no cover
            raise ValueError(f"SizingResult parse error: {exc}") from exc

    @classmethod
    def parse_file(cls, path: str | Path) -> "SizingResult":
        path = Path(path)
        return cls.parse_obj(json.loads(path.read_text(encoding="utf-8")))
