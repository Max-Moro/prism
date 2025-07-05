from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import json
import yaml
from jsonschema import validate, ValidationError
from pydantic import BaseModel, ConfigDict, Field

_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "project.schema.json"
with _SCHEMA_PATH.open(encoding="utf-8") as _fh:
    _PROJECT_SCHEMA = json.load(_fh)

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
        validate(instance=data, schema=_PROJECT_SCHEMA)

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
        from .load_profile import LoadProfile  # noqa: WPS433

        return cls.model_validate(raw)

from typing import TYPE_CHECKING
if TYPE_CHECKING:  # пирует поздний импорт
    from .load_profile import LoadProfile
