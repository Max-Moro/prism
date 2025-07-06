"""
Project / Zone — оболочки над сгенерированными моделями project.schema.json.

* Перехватываем `parse_file` для ручной JSON-Schema проверки
  (как было в прежней реализации) — лишний «второй» слой безопасности.
* Экспортируем `Zone` (из сгенерированного кода) так же, как раньше,
  чтобы юнит-тесты продолжали использовать `Zone.model_construct(...)`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import yaml
from jsonschema import Draft202012Validator, ValidationError as _JSValidationError
from pydantic import ValidationError as _PydanticError

from .load_profile import _LOAD_SCHEMA  # ре-используем из соседнего модуля

# ──────────────────────────────────────────────────────────────────────────────
# сгенерированные модели
from ._gen.project_gen import (  # noqa: WPS433
    PrismProjectSizingFile as _ProjectGen,
    Zone as _ZoneGen,
)

# ---------------------------------------------------------------------- schema
_SCHEMA_PATH = (
    Path(__file__).resolve().parent / ".." / "schemas" / "project.schema.json"
).resolve()
with _SCHEMA_PATH.open(encoding="utf-8") as _fh:
    _PROJECT_SCHEMA = json.load(_fh)

# регистрируем обе схемы, чтобы `$ref` на load_profile работал офф-лайн
from referencing import Registry, Resource  # noqa: WPS433

_SCHEMA_REGISTRY = (
    Registry()
    .with_resources(
        [
            (_PROJECT_SCHEMA["$id"], Resource.from_contents(_PROJECT_SCHEMA)),
            (_LOAD_SCHEMA["$id"], Resource.from_contents(_LOAD_SCHEMA)),
        ]
    )
)


class Project(_ProjectGen):  # type: ignore[misc]
    """Публичная модель Project. Наследуем поля, добавляем parse_file."""

    # ----------------------------------------------------------------- helpers
    @classmethod
    def _validate_jsonschema(cls, data: Dict[str, Any]) -> None:
        Draft202012Validator(
            schema=_PROJECT_SCHEMA, registry=_SCHEMA_REGISTRY
        ).validate(instance=data)

    # ---------------------------------------------------------------- public
    @classmethod
    def parse_file(cls, path: str | Path) -> "Project":
        """Загрузка YAML/JSON + JSON-Schema + Pydantic."""
        path = Path(path)
        with path.open(encoding="utf-8") as fh:
            raw: Dict[str, Any] = yaml.safe_load(fh)

        try:
            cls._validate_jsonschema(raw)
        except _JSValidationError as exc:
            raise ValueError(
                f"Project schema validation failed: {exc.message}"
            ) from exc

        try:
            return cls.model_validate(raw)
        except _PydanticError as exc:
            raise ValueError(f"Project parsing error: {exc}") from exc


# ──────────────────────────────────────────────────────────────────────────────
# Re-export для совместимости с существующим кодом / тестами
Zone = _ZoneGen  # noqa: N816  (оставляем CamelCase — как было)
