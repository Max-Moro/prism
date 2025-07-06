import math
import re

from asteval import Interpreter

from .graph import BlueprintIndex
from .models import SizingResult
from .units import parse_quantity

_WHITELIST = {
    "ceil": math.ceil,
    "min": min,
    "max": max,
}

# eval-формула с подстановкой «64Mi»
_UNIT_TOKEN = re.compile(r"\d+(?:\.\d+)?[KMGkmg]i?|[0-9]+m")


class MiniEvalEngine:
    def __init__(self, blueprints, project):
        self.index  = BlueprintIndex(blueprints)
        self.project = project

    # ------------------------------------------------ helpers -------------
    def _new_interp(self, load_profile):
        ae = Interpreter(usersyms=_WHITELIST, use_numpy=False)
        ae.symtable.update(load_profile.model_dump())
        return ae

    def _subst_units(self, expr: str) -> str:
        """
        Заменяет «64Mi» → «67108864» прямо в строке выражения.
        Работает и для «150m» (millicore).
        """

        def repl(match: re.Match[str]) -> str:  # noqa: WPS110
            return str(parse_quantity(match.group(0)))

        return _UNIT_TOKEN.sub(repl, expr)

    def _eval_expr(self, interp, expr: str) -> float:
        return interp(self._subst_units(expr))

    def _eval_block(self, interp, block, dyn):
        if dyn:
            cpu = self._eval_expr(interp, block["cpu"])
            mem = self._eval_expr(interp, block["memory"])
        else:
            cpu = parse_quantity(block["cpu"])
            mem = parse_quantity(block["memory"])
        return cpu, mem

    # ---------------------------------------------------------------------
    # расчёт одной зоны Project-а
    # ---------------------------------------------------------------------
    def _run_zone(self, zone):
        """
        Возвращает dict-структуру сайзинга **только для данной зоны**:
        {
            "services":          { …technical services… },
            "generic_services":  { …generic services…   },
            "infra":             { …infra deps…         },
            "totals": {          # агрегаты по зоне
                "requests": { "cpu": float, "memory": float },
                "limits":   { "cpu": float, "memory": float },
            }
        }
        """
        # отдельный интерпретатор → переменные = load_profile зоны
        interp   = self._new_interp(zone.load_profile)
        visited  = set()           # чтобы не считать один объект дважды
        result   = {
            "services": {},
            "generic_services": {},
            "infra": {},
            "totals": {
                "requests": {"cpu": 0.0, "memory": 0.0},
                "limits":   {"cpu": 0.0, "memory": 0.0},
            },
        }

        # ---------- корневой набор technical-service исходя из BusinessModule
        roots = []
        if zone.enabled_modules:                         # обычный путь
            for bm_name in zone.enabled_modules:
                if bm_name not in self.index.busmod:
                    raise KeyError(f"BusinessModule '{bm_name}' not found in blueprints")
                _, bm = self.index.busmod[bm_name]
                roots.extend(bm["services"])
        else:                                            # ← fallback для unit-теста
            # если модулей не задано, считаем, что нужны **все** technical-services
            roots = list(self.index.tech.keys())

        # -----------------------------------------------------------------
        # helpers
        # -----------------------------------------------------------------
        def visit_infra(name: str) -> None:
            """Добавляет infra-dependency и её capacity (один раз)."""
            if name in visited:
                return
            visited.add(name)

            bp_obj, infra = self.index.infra[name]
            # capacity: выражения → числа
            capacity = {
                k: (
                    self._eval_expr(interp, v) if isinstance(v, str) else v
                )
                for k, v in infra.get("capacity", {}).items()
            }
            result["infra"][name] = {
                "type": infra["type"],
                "version": infra.get("version"),
                "capacity": capacity,
            }

        def walk(node: str, kind: str) -> None:
            """
            depth-first обход:
            kind = 'technical' | 'generic'
            """
            if node in visited:
                return
            visited.add(node)

            store = self.index.tech if kind == "technical" else self.index.generic
            bp_obj, svc = store[node]

            # ---------- профиль ресурсов
            prof_ref   = svc["resources"]["profile"]
            dyn        = prof_ref.endswith("@dyn")
            prof_name  = prof_ref.replace("@dyn", "")
            prof_map   = bp_obj.model_dump(mode="python").get("resource_profiles", {})
            prof       = prof_map[prof_name]
            section    = "dynamic" if dyn else "static"

            # requests
            req_cpu, req_mem = self._eval_block(
                interp, prof[section]["requests"], dyn
            )

            # limits (могут отсутствовать)
            lim_cpu = lim_mem = 0.0
            if "limits" in prof[section]:
                lim_cpu, lim_mem = self._eval_block(
                    interp, prof[section]["limits"], dyn
                )

            bucket = "services" if kind == "technical" else "generic_services"
            result[bucket][node] = {
                "requests": {"cpu_cores": req_cpu, "memory_bytes": req_mem},
                "limits":   {"cpu_cores": lim_cpu, "memory_bytes": lim_mem},
            }

            # агрегируем
            result["totals"]["requests"]["cpu"]    += req_cpu
            result["totals"]["requests"]["memory"] += req_mem
            result["totals"]["limits"]["cpu"]      += lim_cpu
            result["totals"]["limits"]["memory"]   += lim_mem

            # ---------- рекурсивно по depends_on
            for dep in svc.get("depends_on", []):
                if dep in self.index.generic:
                    walk(dep, "generic")
                elif dep in self.index.infra:
                    visit_infra(dep)
                elif dep in self.index.tech:           # неожиданный, но разрешим
                    walk(dep, "technical")
                else:
                    raise KeyError(f"Unknown dependency '{dep}'")

        # -----------------------------------------------------------------
        # стартуем обход с technical-корней
        # -----------------------------------------------------------------
        for root in roots:
            walk(root, "technical")

        return result

    # ------------------------------------------------ public run ----------
    def run(self) -> SizingResult:
        zones_out = {}
        totals = {
            "requests": {"cpu": 0.0, "memory": 0.0},
            "limits":   {"cpu": 0.0, "memory": 0.0},
        }

        for zone in self.project.zones:
            zres = self._run_zone(zone)
            zones_out[zone.name] = zres

            for t in ("requests", "limits"):
                totals[t]["cpu"]    += zres["totals"][t]["cpu"]
                totals[t]["memory"] += zres["totals"][t]["memory"]

        return SizingResult(details={"zones": zones_out, "totals": totals})
