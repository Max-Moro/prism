"""
LoadProfile — тонкая обёртка над автосгенерированным классом
`project_gen.load_profile.Schema`.

Она:
* добавляет метод `parse_file(path)` с предварительной JSON-Schema
  валидацией (как было раньше);
* остаётся совместимой с `Zone`, потому что наследуется
  от именно того класса, который указан в схеме Project.
"""

from __future__ import annotations

import json
from importlib import resources
from pathlib import Path
from typing import Any, Dict

import yaml
from jsonschema import ValidationError as _JSValidationError, validate as _js_validate
from pydantic import ValidationError as _PydanticError

# ──────────────────────────────────────────────────────────────────────────────
# ⚠️  ВАЖНО: используем _тот_ класс, на который ссылается Zone
from ._gen.project_gen.load_profile import (  # noqa: WPS433
    Schema as _LPBase,
)

# ---------------------------------------------------------------------- schema
_LOAD_SCHEMA = json.loads(
    resources.files("bims.prism.common.schemas")
    .joinpath("load_profile.schema.json")
    .read_text(encoding="utf-8")
)


class LoadProfile(_LPBase):  # type: ignore[misc]
    """
    Публичная модель. Поля наследуются из автоген-класса `Schema`.
    """

    # ----------------------------------------------------------- helpers
    @classmethod
    def _validate_jsonschema(cls, raw: Dict[str, Any]) -> None:
        """Поднимает jsonschema.ValidationError при несоответствии."""
        _js_validate(instance=raw, schema=_LOAD_SCHEMA)

    # ----------------------------------------------------------- public
    @classmethod
    def parse_file(cls, path: str | Path) -> "LoadProfile":
        """
        Читает YAML/JSON → JSON-Schema → Pydantic.
        Поддерживает вариант с обёрткой `load_profile: { ... }`.
        """
        path = Path(path)
        with path.open(encoding="utf-8") as fh:
            raw: Dict[str, Any] = yaml.safe_load(fh)

        data = raw.get("load_profile", raw)  # unwrap, если нужно

        try:
            cls._validate_jsonschema(data)
        except _JSValidationError as exc:
            raise ValueError(
                f"LoadProfile JSON-Schema validation failed: {exc.message}"
            ) from exc

        try:
            return cls.model_validate(data)
        except _PydanticError as exc:
            raise ValueError(f"LoadProfile parsing error: {exc}") from exc
