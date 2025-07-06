from pathlib import Path
from typing import Any, Dict

import json
import yaml
from jsonschema import validate as _js_validate, ValidationError as _JSValidationError
from pydantic import BaseModel, ConfigDict, Field

# -------------------------------------------------- load ResourceProfile schema once
_RS_SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent / "schemas" / "resource_profile.schema.json"
)
with _RS_SCHEMA_PATH.open(encoding="utf-8") as _fh:
    _RESOURCE_SCHEMA = json.load(_fh)


class Blueprint(BaseModel):
    """Упрощённое представление Blueprint-файла (draft)."""

    kind: str = Field(..., pattern=r"^[A-Za-z]+$")
    team: str
    version: str

    # Разрешаем лишние поля, пока схема не финализирована
    model_config = ConfigDict(extra="allow")

    # --- helpers ---------------------------------------------------------
    @classmethod
    def _validate_resource_profiles(
        cls, data: Dict[str, Any], *, src: Path
    ) -> None:
        """Пробегаемся по всем `resource_profiles` и валидируем схемой."""
        for name, profile in data.get("resource_profiles", {}).items():
            try:
                _js_validate(instance=profile, schema=_RESOURCE_SCHEMA)
            except _JSValidationError as e:  # pragma: no cover
                raise ValueError(
                    f"[{src.name}] ResourceProfile '{name}' invalid: {e.message}"
                ) from e

    @classmethod
    def parse_file(cls, path: str | Path) -> "Blueprint":
        """
        YAML → dict → проверяем ResourceProfile → Pydantic-модель.
        Полная валидация Blueprint появится позже (Sprint P0-1).
        """
        path = Path(path)
        with path.open(encoding="utf-8") as fh:
            data: Dict[str, Any] = yaml.safe_load(fh)

        # 🌟 Новая проверка
        cls._validate_resource_profiles(data, src=path)

        return cls.model_validate(data)
