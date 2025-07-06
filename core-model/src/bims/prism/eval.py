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

    def run(self) -> SizingResult:
        from .models import SizingResult  # локальный импорт, чтобы избежать циклов

        result = {"services": {}, "totals": {"cpu": 0.0, "memory": 0.0}}

        for bp in self.bp:                            # список/итератор Blueprint-ов
            for name, svc in bp.technical_services.items():
                profile_ref = svc["resources"]["profile"]
                if profile_ref.endswith("@dyn"):
                    profile_name = profile_ref.replace("@dyn", "")
                    section = "dynamic"
                else:
                    profile_name = profile_ref
                    section = "static"

                prof = bp.resource_profiles[profile_name][section]["requests"]

                # --- CPU --------------------------------------------------
                if section == "dynamic":
                    cpu = self.eval(prof["cpu"])
                    mem = self.eval(prof["memory"])
                else:                           # static
                    cpu = parse_quantity(prof["cpu"])
                    mem = parse_quantity(prof["memory"])

                result["services"][name] = {
                    "cpu_cores":     cpu,
                    "memory_bytes":  mem,
                }
                result["totals"]["cpu"]    += cpu
                result["totals"]["memory"] += mem

        return SizingResult(details=result)

