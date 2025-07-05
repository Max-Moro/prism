import math
from typing import Any
from asteval import Interpreter

_WHITELIST = {
    "ceil": math.ceil,
    "min": min,
    "max": max,
}

class MiniEvalEngine:
    def __init__(self, blueprint, load_profile):
        self.bp = blueprint
        self.load = load_profile
        self._ae = Interpreter(usersyms=_WHITELIST, use_numpy=False)

    def eval(self, expr: str, **vars: Any) -> Any:
        return self._ae(expr, **vars)

    # TODO: основной расчёт
    def run(self):
        raise NotImplementedError("Sprint 1 — реализуем позже")
