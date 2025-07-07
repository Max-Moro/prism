# **PRISM Core-Model**

> Расчётный движок, CLI-утилита и контрактные схемы
> (уровни **Blueprint ↔ LoadProfile ↔ SizingResult**).

---

## 1 Назначение

* **Вход**

  * `*.sizing.yaml` — файл проекта (зоны + BusinessModule).
  * Набор `*.blueprint.yaml` — формулы и граф зависимостей всех команд.
* **Вычисляет** ресурсы (CPU / RAM / Storage) для Technical, Generic и Infra-сервисов в каждой зоне.
* **Вывод** — объект **`SizingResult`** (см. схему в *prism-common*), сериализуемый в JSON:

```jsonc
{
  "zones": { "Prod": …, "Test": … },
  "totals": { "requests": { … }, "limits": { … } },
  "infra_totals": { "postgres": { "storage_gb": 420 } }
}
```

> gRPC-API для Spring-Service появится в v0.5 (см. Roadmap).

---

## 2 Быстрый старт (локальная разработка)

```bash
git clone https://github.com/bims/prism.git
cd prism
python -m venv .venv && source .venv/bin/activate

# 1) ставим shared-пакет и ядро
pip install -e common       # prism-common  (schemas, units)
pip install -e core-model   # prism-core

# 2) Справка CLI
python -m bims.prism.cli --help

# 3) Smoke-тесты ядра
pytest core-model/tests -q

# 4) End-to-end YAML → JSON
python -m bims.prism.cli calculate \
  examples/acme.project.yaml examples/blueprints \
  | jq '.totals'
```

---

## 3 Каталог `core-model` (актуальный layout)

```text
core-model/
├─ pyproject.toml         # wheel prism-core
├─ src/
│  └─ bims/prism/
│      ├─ cli.py          # Typer entrypoint
│      ├─ eval.py         # MiniEvalEngine (asteval)
│      ├─ graph.py        # BlueprintIndex + DFS
│      ├─ units.py        # shim → re-export из prism-common
│      ├─ models/
│      │   ├─ blueprint.py
│      │   ├─ load_profile.py
│      │   ├─ sizing_result.py
│      │   └─ _gen/       # ← авто-сгенерированные Pydantic-классы
│      └─ schemas/        # ← ТОЛЬКО blueprint / resource_profile
├─ scripts/
│  └─ gen_models.py       # генерация моделей из JSON-Schema
├─ tests/
│  ├─ unit/
│  └─ integration/
└─ README.md  ← **этот файл**
```

*JSON-схемы `sizing_result`, `load_profile` и `project` теперь хранится в пакете **prism-common**
(`common/src/bims/prism/common/schemas`).*

---

## 4 Мини-движок формул (`eval.py`)

* Безопасный интерпретатор **asteval**.
* Поддерживает «кавычки-единицы» (`128Mi`, `150m`), арифметику и функции из `_WHITELIST` (`ceil`, `min`, `max`, …).
* Requests / Limits, динамические профили `@dyn`, рекурсия `depends_on`.

---

## 5 CLI `prism-cli`

```bash
usage: prism-cli calculate [OPTIONS] PROJECT_FILE [BLUEPRINT_DIR]

Options:
  --json-out FILE  Save result instead of stdout
  --help
```

Пример:

```bash
python -m bims.prism.cli calculate \
  projects/acme.sizing.yaml blueprints \
  --json-out out/acme.result.json
```

---

## 6 Качество кода

| Команда                             | Что проверяет                        |
| ----------------------------------- | ------------------------------------ |
| `ruff core-model/src`               | стиль + авто-импорт                  |
| `black --check core-model/src`      | форматирование                       |
| `mypy core-model/src`               | статический анализ (Pydantic v2)     |
| `pytest -m unit` / `-m integration` | юнит / e2e-тесты                     |
| `scripts/gen_models.py`             | актуальность сгенерированных моделей |

> `pre-commit install` — запускает ruff/black при каждом commit.

---

## 7 Зависимости (файл *pyproject.toml*)

| Категория | Пакет                                                                       | Причина                     |
| --------- | --------------------------------------------------------------------------- | --------------------------- |
| Runtime   | `prism-common`                                                              | shared `units`, JSON-schema |
| Runtime   | `pydantic`                                                                  | строгие модели              |
| Runtime   | `PyYAML`                                                                    | YAML-парсер                 |
| Runtime   | `typer[all]`                                                                | CLI                         |
| Runtime   | `asteval`                                                                   | формульный движок           |
| Runtime   | `jsonschema`                                                                | runtime-валидация           |
| Dev       | `ruff`, `black`, `mypy`, `pytest`, `pytest-cov`, `datamodel-code-generator` |                             |

---

## 8 CI (единый workflow)

`.github/workflows/ci.yml`:

```yaml
jobs:
  test:
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: |
          pip install -e common
          pip install -e core-model
          pip install pytest ruff black
      - run: ruff .
      - run: black --check .
      - run: python core-model/scripts/gen_models.py && git diff --exit-code
      - run: pytest -m "unit or integration" --cov=bims.prism
```

---

## 9 Расширение

| Что нужно              | Где править                                                   |
| ---------------------- | ------------------------------------------------------------- |
| Новое поле LoadProfile | `models/load_profile.py` + `schemas/load_profile.schema.json` |
| Новая формула          | `eval.py` или вынос в `evaluator/*.py`                        |
| Новый юнит ресурса     | `prism-common.units`                                          |
| gRPC-слой              | `api/proto/*.proto` + `grpc_server.py`                        |

---

## 10 Roadmap

* [Roadmap Core-Model](./ROADMAP.md)
* [Общая Roadmap проекта](../docs/roadmap.md)

---
