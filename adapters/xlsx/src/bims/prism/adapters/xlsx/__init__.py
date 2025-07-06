"""
XLSX-Adapter (skeleton).

Фасадная функция build_report() имитирует поведение,
которое описано в docs/adapters_report_architecture.md.
"""

from .builder import XlsxAdapter

__all__ = ["build_report", "XlsxAdapter"]

def build_report(sizing_result, *, theme: str = "default") -> bytes:  # noqa: ANN001
    return XlsxAdapter(theme=theme).build(sizing_result)
