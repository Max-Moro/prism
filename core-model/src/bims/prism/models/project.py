from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import yaml
from jsonschema import Draft202012Validator, ValidationError
from pydantic import BaseModel, ConfigDict, Field
from referencing import Registry, Resource

# --- load both schemas once ------------------------------------------------
_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "project.schema.json"
with _SCHEMA_PATH.open(encoding="utf-8") as _fh:
    _PROJECT_SCHEMA = json.load(_fh)

# load_profile schema (already loaded in LoadProfile module, reuse)
from .load_profile import _LOAD_SCHEMA   # noqa: WPS433

# registry «URL → объект» для резолвера
_SCHEMA_REGISTRY = (
    Registry()
    .with_resources([
        (_PROJECT_SCHEMA["$id"], Resource.from_contents(_PROJECT_SCHEMA)),
        (_LOAD_SCHEMA["$id"],    Resource.from_contents(_LOAD_SCHEMA)),
    ])
)

# --- Pydantic -------------------------------------------------------------
class Zone(BaseModel):
    name: str
    enabled_modules: List[str] = Field(min_length=1)
    load_profile: "LoadProfile"

    model_config = ConfigDict(extra="forbid")


class Project(BaseModel):
    customer: str
    zones: List[Zone] = Field(min_length=1)

    model_config = ConfigDict(extra="forbid")

    # ---------------------------------------------------------- helpers ----
    @classmethod
    def _validate_jsonschema(cls, data: Dict[str, Any]) -> None:
        Draft202012Validator(
            schema=_PROJECT_SCHEMA,
            registry=_SCHEMA_REGISTRY,      # ⬅ локальный кэш
        ).validate(instance=data)

    @classmethod
    def parse_file(cls, path: str | Path) -> "Project":
        path = Path(path)
        with path.open(encoding="utf-8") as fh:
            raw: Dict[str, Any] = yaml.safe_load(fh)

        try:
            cls._validate_jsonschema(raw)
        except ValidationError as e:
            raise ValueError(f"Project schema validation failed: {e.message}") from e

        # импорт здесь, чтобы избежать циклов

        return cls.model_validate(raw)

# «живой» импорт, а не только TYPE_CHECKING
from .load_profile import LoadProfile  # noqa: WPS433

Zone.model_rebuild()
Project.model_rebuild()