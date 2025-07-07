from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List

import openpyxl
from bims.prism.common.units import format_bytes
from jinja2 import Environment, FileSystemLoader

# ─────────────────────────── Jinja env (оставляем: пригодится позже)
_TEMPL_DIR = Path(__file__).parent / "templates"
_J2 = Environment(loader=FileSystemLoader(str(_TEMPL_DIR)), autoescape=False)


class XlsxAdapter:
    def __init__(self, *, theme: str = "default") -> None:
        self.theme = theme

    def _normalize(self, sizing_result) -> Dict[str, Any]:  # noqa: ANN001
        """Принимаем либо dict, либо Pydantic-объект SizingResult."""
        if hasattr(sizing_result, "model_dump"):
            return sizing_result.model_dump()
        return sizing_result

    # ----------------------------------------------------------
    def build(self, sizing_result):  # noqa: ANN001
        """
        Возвращает XLSX с листом «Totals».
        Требуются только поля zones[*].totals.{requests,limits}.
        """
        data = self._normalize(sizing_result)

        zones_ctx = []
        for name, z in data["zones"].items():
            rq = z["totals"]["requests"]
            lm = z["totals"]["limits"]
            zones_ctx.append(
                {
                    "name": name,
                    "req_cpu": round(rq["cpu"], 3),
                    "req_mem": format_bytes(rq["memory"], precision=0),
                    "lim_cpu": round(lm["cpu"], 3),
                    "lim_mem": format_bytes(lm["memory"], precision=0),
                }
            )

        # ───── собрать книгу (write_only) через append
        wb = openpyxl.Workbook(write_only=True)
        ws = wb.create_sheet("Totals")  # type: ignore[arg-type]

        # шапка
        header: List[str] = [
            "Zone",
            "CPU req (cores)",
            "Memory req",
            "CPU lim",
            "Memory lim",
        ]
        ws.append(header)

        # данные
        for z in zones_ctx:
            ws.append(
                [
                    z["name"],
                    z["req_cpu"],
                    z["req_mem"],
                    z["lim_cpu"],
                    z["lim_mem"],
                ]
            )

        buf = BytesIO()
        wb.save(buf)
        return buf.getvalue()
