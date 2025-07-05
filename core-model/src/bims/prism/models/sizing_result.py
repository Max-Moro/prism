from typing import Any, Dict

from pydantic import BaseModel, Field


class SizingResult(BaseModel):
    """Пока просто произвольный словарь с результатами."""

    details: Dict[str, Any] = Field(default_factory=dict)
