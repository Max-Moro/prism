from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import yaml
from jsonschema import validate, ValidationError
from pydantic import BaseModel, ValidationError as PydanticError, ConfigDict

# Загружаем JSON-Schema один раз при импорте
_SCHEMAPATH = Path(__file__).resolve().parent.parent / "schemas" / "load_profile.schema.json"
with _SCHEMAPATH.open(encoding="utf-8") as _fh:
    _LOAD_SCHEMA = json.load(_fh)


class LoadProfile(BaseModel):
    """Набор входных нагрузочных параметров."""

    online_users: int
    total_users: int
    rps: int
    rps_p95: int
    jobs_rate: int | None = None
    structured_data_gb: float
    unstructured_data_gb: float

    # schema уже ловит опечатки, но forbid защитит от ручного создания объекта
    model_config = ConfigDict(extra="forbid")

    # --------------------------------------------------------------------- #
    @classmethod
    def _validate_jsonschema(cls, data: Dict[str, Any]) -> None:
        """Бросает ValidationError jsonschema при несоответствии."""
        validate(instance=data, schema=_LOAD_SCHEMA)

    @classmethod
    def parse_file(cls, path: str | Path) -> "LoadProfile":
        """
        Читает YAML/JSON, валидирует по JSON-Schema, затем парсит Pydantic.
        Поддерживает вариант с обёрткой `load_profile: {...}`.
        """
        path = Path(path)
        with path.open(encoding="utf-8") as fh:
            raw: Dict[str, Any] = yaml.safe_load(fh)

        # unwrap, если файл содержит корневой ключ load_profile
        data = raw.get("load_profile", raw)

        # ↓ jsonschema — ловим опечатки и неверные типы раньше Pydantic
        try:
            cls._validate_jsonschema(data)
        except ValidationError as e:
            raise ValueError(f"LoadProfile JSON-Schema validation failed: {e.message}") from e

        # ↓ Pydantic — строгая типизация + post-processing
        try:
            return cls.model_validate(data)
        except PydanticError as e:  # даст красивый str()
            raise ValueError(f"LoadProfile parsing error: {e}") from e
