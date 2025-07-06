# **PRISM Core-Model**

> Движок вычислений, CLI-утилита и контрактная модель данных  
> (уровни *Blueprint ↔ Load Profile ↔ Sizing Result*).

---

## 1. Назначение модуля

* **Принимает**:  
  * **Project-файл** заказчика (`*.sizing.yaml`) — описывает зоны и
    включённые BusinessModule.  
  * Каталог или набор `Blueprint`-ов (`*.blueprint.yaml`) — формулы и граф зависимостей
    всех команд.
* **Вычисляет** ресурсы (CPU/RAM/Storage GB/…) для:
  * всех Technical / Generic сервисов,
  * их зависимостей **Infrastructure** (PostgreSQL, Kafka и др.),
  * каждой **зоны** проекта (Prod, Test, DR …).
* **Возвращает**:
  * JSON-объект сайзинга вида  
    `{ zones: { Prod: {...}, Test: {...} }, totals: {...} }`
  * (roadmap v0.5) gRPC API для **service**-модуля

---

## 2. Быстрый старт (локальный)

```bash
# клонируем монорепу и переходим
git clone https://github.com/bims/prism.git
cd prism

# создаём виртуальное окружение
py -3.12 -m venv .venv
.venv\Scripts\activate        # Windows PowerShell

# ставим зависимости core-model
pip install -r core-model/requirements.txt -r core-model/requirements_dev.txt
```

Проверяем:

```bash
# справка CLI
python -m bims.prism.cli --help

# smoke-тесты
pytest -m unit
```

---

## 3. Структура каталога `core-model`

```text
core-model/
├─ src/
│  └─ bims/
│      └─ prism/
│          ├─ cli.py            # Typer-CLI (entrypoint)
│          ├─ eval.py           # MiniEvalEngine (asteval-based)
│          ├─ units.py          # parse_quantity / human-units
│          ├─ graph.py          # BlueprintIndex + DFS
│          ├─ models/
│          │   ├─ blueprint.py
│          │   ├─ load_profile.py
│          │   ├─ sizing_result.py
│          │   └─ _gen/          # ← авто-сгенерированные Pydantic-классы
│          └─ schemas/
│              ├─ load_profile.schema.json
│              ├─ project.schema.json
│              ├─ blueprint.schema.json
│              └─ resource_profile.schema.json
├─ scripts/
│  └─ gen_models.py      # one-shot генерация моделей из JSON-Schema
├─ tests/
│  ├─ unit/
│  └─ integration/
├─ requirements.txt
├─ requirements_dev.txt
├─ pytest.ini
└─ README.md      ← **этот файл**
```

### Зачем `src/`
Изоляция исходников от метаданных; IDE автоматически добавит его в PYTHONPATH.

---

## 4. Мини-движок формул (`eval.py`)

* Основан на **asteval** (Python-safe подсетевой интерпретатор).
* Белый список функций (`ceil`, `min`, `max`, …​) задаётся в `_WHITELIST`.
* Уже поддерживает «кавычки-единицы» (`"128Mi" → bytes`, `"150m" → cores`),
  динамические выражения `0.02 + 0.00002 * online_users`,
  requests / limits и рекурсивные `depends_on`.

---

## 5. CLI `prism-cli`

```bash
usage: prism-cli calculate [OPTIONS] PROJECT_FILE [BLUEPRINT_DIR]

Arguments:
  PROJECT_FILE    customer sizing file (`*.sizing.yaml`)
  [BLUEPRINT_DIR] Folder with `*.blueprint.yaml` (default: `blueprints/`)

Options:
  --json-out FILE  файл, куда сохранить результат (иначе вывод в stdout)
  --help           Show this message and exit.
```

Пример:

```bash
python -m bims.prism.cli calculate ^
  projects\\acme.sizing.yaml ^
  blueprints\\ ^
  --json-out out\\acme.result.json
```

---

## 6. Разработка

### 6.1 Проверка качества

| Команда                       | Что делает                               |
|-------------------------------|------------------------------------------|
| `ruff src tests`             | быстрый линт + авто-импорт               |
| `black src tests`            | автоформатирование                       |
| `mypy src`                   | статический анализ типов (Pydantic v2)   |
| `pytest -m unit`             | юнит-тесты                               |
| `pytest -m integration`      | e2e / I-O / CLI-smoke                    |
| `pytest --cov`               | покрытие                                 |
| `scripts/gen_models.py`      | пересгенерировать Pydantic модели        |
| `pre-commit run --all`       | локальный запуск всех хуков              |

> **Совет:** `pre-commit install` — линтер и black проверятся при каждом `git commit`.

### 6.2 Стандарты кода

* **Conventional Commits** (`feat:`, `fix:`, `chore:` …​)
* **Black + Ruff** — единственный форматтер/линтер
* Type hints обязательны в публичных API (`models/*.py`, `eval.py`)

---

## 7. Зависимости

| Категория | Пакет                         | Версия                     | Причина пина                             |
|-----------|-------------------------------|----------------------------|------------------------------------------|
| Runtime   | pydantic                      | 2.7.1                      | модели данных                            |
| Runtime   | PyYAML                        | 6.0.2                      | парсинг YAML                             |
| Runtime   | typer                         | 0.12.3                     | CLI                                      |
| Runtime   | asteval                       | 0.9.31                     | движок формул                            |
| Runtime   | jsonschema                    | 4.22                       | валидация Project/Load Profile           |
| Runtime   | **click**                     | **8.1.7**                  | ⬅ фикс на 8.2+ (incompatible with Typer) |
| Dev       | pytest / pytest-cov           | 8.3.1 / 5.0.0              | тесты + покрытие                         |
| Dev       | ruff, black, mypy, pre-commit | см. `requirements_dev.txt` | стиль / типы                             |
| Dev       | **datamodel-code-generator**  | 0.31.2                     | автоген строгих Pydantic моделей         |

---

## 8. Запуск тестов в CI

`.github/workflows/core-model.yml`

```yaml
name: core-model
on:
  push:
    paths: ["core-model/**", ".github/workflows/core-model.yml"]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r core-model/requirements.txt -r core-model/requirements_dev.txt
      - run: ruff core-model/src core-model/tests
      - run: black --check core-model/src core-model/tests
      # убедиться, что сгенерированные модели свежие
      - run: python ./core-model/scripts/gen_models.py && git diff --exit-code
      - run: pytest core-model/tests -m "unit or integration" --cov=bims.prism
```

---

## 9. Как расширять

| Что нужно | Куда писать                                           | Tips                                                                 |
|-----------|-------------------------------------------------------|----------------------------------------------------------------------|
| Новое поле Load Profile | `models/load_profile.py` + `load_profile.schema.json` | не забудьте обновить `Project.schema.json`, `fixtures/` и unit-тесты |
| Новое правило формулы   | `eval.py` или отдельный `evaluator/*.py`              | добавьте в `_WHITELIST` или передайте через `Interpreter.symtable`   |
| Новый тип единиц (IOPS) | `units.py`                                            | добавить в `_UNIT_TOKEN` и `_MULTIPLIER`                             |
| gRPC API                | `api/proto/*.proto` → `buf generate`                  | затем adapter layer в `grpc_server.py`                               |

---

## 10. Дорожная карта Core-Model

* [Актуальная дорожная карта для Core-Model](./ROADMAP.md)
* [Полная Roadmap](../docs/roadmap.md)

