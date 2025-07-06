from collections import defaultdict


class BlueprintIndex:
    """
    Быстрый lookup: имя → (blueprint-obj, yaml-dict).
    Считаем, что имена уникальны (договоримся на CI-валидации).
    """
    def __init__(self, blueprints):
        self.tech, self.generic, self.infra, self.busmod = {}, {}, {}, {}
        self._ovr_map = defaultdict(lambda: {"teams": []})  # (kind,name) → dict

        for bp in blueprints:
            data = bp.model_dump(mode="python")      # extra-ключи внутри
            self._merge(self.tech,     "technical_service",      data.get("technical_services", {}),      bp)
            self._merge(self.generic,  "generic_service",        data.get("generic_services",  {}),      bp)
            self._merge(self.infra,    "infra_dependency",       data.get("infra_dependencies", {}),     bp)
            self._merge(self.busmod,   "business_module",        data.get("business_modules", {}),       bp)

        # итоговый список warning-ов
        self.overrides = [
            {"name": name, "kind": kind, "teams": info["teams"]}
            for (kind, name), info in self._ovr_map.items()
            if len(info["teams"]) > 1
        ]

    # ------------------------------------------------ private helpers
    def _merge(self, store, kind: str, items: dict, bp):
        for name, val in items.items():
            if name in store:
                prev_bp, _ = store[name]
                if prev_bp.team != bp.team:
                    key = (kind, name)
                    if not self._ovr_map[key]["teams"]:
                        self._ovr_map[key].update({"name": name, "kind": kind})
                        self._ovr_map[key]["teams"].append(prev_bp.team)
                    if bp.team not in self._ovr_map[key]["teams"]:
                        self._ovr_map[key]["teams"].append(bp.team)
            store[name] = (bp, val)
