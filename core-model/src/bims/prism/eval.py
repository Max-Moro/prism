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

        self._visited = set()  # имена уже посчитанных service/infra

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

    def _walk_dep(self, bp, name, kind):
        """
        kind = 'technical' | 'generic'
        """
        if name in self._visited:
            return
        self._visited.add(name)

        # --- technical / generic ------------------------------------------
        if kind in ("technical", "generic"):
            src = (bp.technical_services if kind == "technical"
                   else bp.generic_services)[name]
            profile_ref = src["resources"]["profile"]
            dyn = profile_ref.endswith("@dyn")
            prof_name = profile_ref.replace("@dyn", "")
            prof = bp.resource_profiles[prof_name]

            req_cpu, req_mem = self._eval_block(
                prof["dynamic" if dyn else "static"]["requests"], dyn
            )
            lim_cpu, lim_mem = (0, 0)
            lims = prof["dynamic" if dyn else "static"].get("limits")
            if lims:
                lim_cpu, lim_mem = self._eval_block(lims, dyn)

            bucket = "services" if kind == "technical" else "generic_services"
            self._result[bucket][name] = {
                "requests": {"cpu_cores": req_cpu, "memory_bytes": req_mem},
                "limits": {"cpu_cores": lim_cpu, "memory_bytes": lim_mem},
            }
            self._result["totals"]["requests"]["cpu"] += req_cpu
            self._result["totals"]["requests"]["memory"] += req_mem
            self._result["totals"]["limits"]["cpu"] += lim_cpu
            self._result["totals"]["limits"]["memory"] += lim_mem

            # --- рекурсивно идём по зависимостям ---------------------------
            for dep in src.get("depends_on", []):
                if dep in bp.generic_services:
                    self._walk_dep(bp, dep, "generic")
                elif dep in bp.infra_dependencies:
                    self._visit_infra(bp, dep)
                else:
                    raise KeyError(f"Unknown dependency: {dep}")

    def _visit_infra(self, bp, name):
        if name in self._visited:
            return
        self._visited.add(name)

        infra = bp.infra_dependencies[name]
        cap = {}
        for k, expr in infra.get("capacity", {}).items():
            cap[k] = self.eval(expr) if isinstance(expr, str) else expr

        self._result["infra"][name] = {
            "type": infra["type"],
            "version": infra.get("version"),
            "capacity": cap,
        }

    def run(self) -> SizingResult:
        self._result = {
            "services": {},
            "generic_services": {},
            "infra": {},
            "totals": {
                "requests": {"cpu": 0.0, "memory": 0.0},
                "limits": {"cpu": 0.0, "memory": 0.0},
            },
        }

        for bp in self.bp:
            for root in bp.technical_services.keys():
                self._walk_dep(bp, root, "technical")

        return SizingResult(details=self._result)

