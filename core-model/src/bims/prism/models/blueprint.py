from pathlib import Path
from typing import Any, Dict

import yaml
from pydantic import BaseModel, ConfigDict, Field


class Blueprint(BaseModel):
    """Упрощённое представление Blueprint-файла (draft)."""

    kind: str = Field(..., pattern=r"^[A-Za-z]+$")
    team: str
    version: str

    # Разрешаем лишние поля, пока схема не финализирована
    model_config = ConfigDict(extra="allow")

    # --- helpers ---------------------------------------------------------
    @classmethod
    def parse_file(cls, path: str | Path) -> "Blueprint":
        """Загружает YAML/JSON-файл в объект Blueprint."""
        path = Path(path)
        with path.open(encoding="utf-8") as fh:
            data: Dict[str, Any] = yaml.safe_load(fh)
        return cls.model_validate(data)
