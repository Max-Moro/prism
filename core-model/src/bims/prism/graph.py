
class BlueprintIndex:
    """
    Быстрый lookup: имя → (blueprint-obj, yaml-dict).
    Считаем, что имена уникальны (договоримся на CI-валидации).
    """
    def __init__(self, blueprints):
        self.tech, self.generic, self.infra, self.busmod = {}, {}, {}, {}

        for bp in blueprints:
            data = bp.model_dump(mode="python")      # extra-ключи внутри
            self.tech.update(
                {k: (bp, v) for k, v in data.get("technical_services", {}).items()}
            )
            self.generic.update(
                {k: (bp, v) for k, v in data.get("generic_services", {}).items()}
            )
            self.infra.update(
                {k: (bp, v) for k, v in data.get("infra_dependencies", {}).items()}
            )
            self.busmod.update(
                {k: (bp, v) for k, v in data.get("business_modules", {}).items()}
            )
