from pathlib import Path
from typing import Any, Dict

import yaml
from pydantic import BaseModel, ConfigDict


class LoadProfile(BaseModel):
    """Набор входных нагрузочных параметров (stub)."""

    online_users: int | None = None
    total_users: int | None = None
    rps: int | None = None
    rps_p95: int | None = None
    jobs_rate: int | None = None
    structured_data_gb: float | None = None
    unstructured_data_gb: float | None = None

    # Принимаем дополнительные поля, чтобы не падать раньше времени
    model_config = ConfigDict(extra="allow")

    # --- helpers ---------------------------------------------------------
    @classmethod
    def parse_file(cls, path: str | Path) -> "LoadProfile":
        """Читает YAML/JSON; допускает обёртку `load_profile:`."""
        path = Path(path)
        with path.open(encoding="utf-8") as fh:
            raw: Dict[str, Any] = yaml.safe_load(fh)

        data = raw.get("load_profile", raw)  # unwrap если нужно
        return cls.model_validate(data)
