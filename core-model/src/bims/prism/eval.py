import math
import re
from typing import Any

from asteval import Interpreter

from .models import SizingResult
from .units import parse_quantity

_WHITELIST = {
    "ceil": math.ceil,
    "min": min,
    "max": max,
}

_UNIT_TOKEN = re.compile(r"\d+(?:\.\d+)?[KMGkmg]i?|[0-9]+m")


def _subst_units(expr: str) -> str:
    """
    Заменяет «64Mi» → «67108864» прямо в строке выражения.
    Работает и для «150m» (millicore).
    """

    def repl(match: re.Match[str]) -> str:  # noqa: WPS110
        return str(parse_quantity(match.group(0)))

    return _UNIT_TOKEN.sub(repl, expr)

class MiniEvalEngine:
    def __init__(self, blueprints, load_profile):
        self.bp = blueprints
        self.load = load_profile
        self._ae = Interpreter(usersyms=_WHITELIST, use_numpy=False)

        # все переменные из LoadProfile сразу кладём в символьную таблицу
        self._ae.symtable.update(load_profile.model_dump())

    def eval(self, expr: str) -> Any:
        expr_norm = _subst_units(expr)
        return self._ae(expr_norm)

    def _eval_block(self, block: dict[str, str], dyn: bool) -> tuple[float, float]:
        """
        Возвращает (cpu, mem) — cpu в *ядрах*, memory в *байтах*.
        """
        if dyn:
            cpu = self.eval(block["cpu"])
            mem = self.eval(block["memory"])
        else:
            cpu = parse_quantity(block["cpu"])
            mem = parse_quantity(block["memory"])
        return cpu, mem

    def run(self) -> SizingResult:
        result = {
            "services": {},
            "totals": {
                "requests": {"cpu": 0.0, "memory": 0.0},
                "limits": {"cpu": 0.0, "memory": 0.0},
            },
        }

        for bp in self.bp:
            for name, svc in bp.technical_services.items():
                prof_ref = svc["resources"]["profile"]
                dyn = prof_ref.endswith("@dyn")
                prof_name = prof_ref.replace("@dyn", "")

                prof = bp.resource_profiles[prof_name]

                # ---------- requests ----------
                req_block = (prof["dynamic" if dyn else "static"]["requests"])
                req_cpu, req_mem = self._eval_block(req_block, dyn)

                # ---------- limits (optional) ----------
                lim_cpu, lim_mem = None, None
                limits_present = "limits" in prof["dynamic" if dyn else "static"]
                if limits_present:
                    lim_block = (prof["dynamic" if dyn else "static"]["limits"])
                    lim_cpu, lim_mem = self._eval_block(lim_block, dyn)

                # ---------- записываем ----------
                svc_entry = {
                    "requests": {"cpu_cores": req_cpu, "memory_bytes": req_mem},
                }
                if limits_present:
                    svc_entry["limits"] = {
                        "cpu_cores": lim_cpu,
                        "memory_bytes": lim_mem,
                    }
                result["services"][name] = svc_entry

                # ---------- агрегаты ----------
                result["totals"]["requests"]["cpu"] += req_cpu
                result["totals"]["requests"]["memory"] += req_mem
                if limits_present:
                    result["totals"]["limits"]["cpu"] += lim_cpu
                    result["totals"]["limits"]["memory"] += lim_mem

        return SizingResult(details=result)

