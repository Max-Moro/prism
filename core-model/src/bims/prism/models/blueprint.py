"""
Blueprint — сознательно **ручная** обёртка.

Почему не используем автоген прямо сейчас:
* datamodel-code-generator по-прежнему вставляет `regex=` и `__root__`
  (что ломается на Pydantic v2).
* Этого достаточно, чтобы импорт модуля упал ещё до первого выполнения кода.

Поэтому:
1. Оставляем минимальную структуру (kind/team/version) — для остального
   работаем словарём (`extra="allow"`).
2. Добавляем проверку всех `resource_profiles`
   через отдельную JSON-Schema (`resource_profile.schema.json`).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import yaml
from jsonschema import validate as _js_validate, ValidationError as _JSValidationError
from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------- schema
_RP_SCHEMA_PATH = (
    Path(__file__).resolve().parent / ".." / "schemas" / "resource_profile.schema.json"
).resolve()
with _RP_SCHEMA_PATH.open(encoding="utf-8") as _fh:
    _RP_SCHEMA = json.load(_fh)


class Blueprint(BaseModel):
    """Упрощённая, но рабочая модель Blueprint-файла."""

    kind: str = Field(..., pattern=r"^[A-Za-z]+$")
    team: str = Field(..., pattern=r"^[a-z0-9-]+$")
    version: str

    # позволяем лишние ключи внутри blueprint-yaml
    model_config = ConfigDict(extra="allow")

    # ---------------------------------------------------------------- helpers
    @classmethod
    def _validate_resource_profiles(cls, data: Dict[str, Any], src: Path) -> None:
        """lint всех resource_profiles через отдельную JSON-Schema."""
        for name, profile in data.get("resource_profiles", {}).items():
            try:
                _js_validate(instance=profile, schema=_RP_SCHEMA)
            except _JSValidationError as exc:
                raise ValueError(
                    f"[{src.name}] ResourceProfile '{name}' invalid: {exc.message}"
                ) from exc

    # ---------------------------------------------------------------- public
    @classmethod
    def parse_file(cls, path: str | Path) -> "Blueprint":
        """YAML → dict → проверка ResourceProfile → Pydantic-модель."""
        path = Path(path)
        with path.open(encoding="utf-8") as fh:
            data: Dict[str, Any] = yaml.safe_load(fh)

        cls._validate_resource_profiles(data, src=path)
        return cls.model_validate(data)
