# PRISM **Core-Model** – Roadmap  

> **Ревизия:** 06.07.2025**  
> Файл ведётся внутри каталога `core-model` и обновляется после каждой итерации: строки из «Планируется» переносятся в «Сделано», при необходимости добавляются новые задачи.

---

## Что **уже сделано** (v0.3-alpha, Sprint 0 – 5)

| Блок                                  | Конкретные таски | Описание реализации / отличия от плана |
|---------------------------------------|------------------|----------------------------------------|
| **Infrastructure / Project skeleton** | Каталог `core-model`, layout `src/`, `tests/`, `requirements*`, `.gitignore`. | Совпадает с корпоративным шаблоном. |
| **CLI / Entry point**                 | Typer-CLI `calculate`; поддержка `--json-out`. | Ленивый импорт моделей. |
| **Data models (Pydantic)**            | Заглушки `Blueprint`, `LoadProfile`, `Project`, `SizingResult`; JSON-Schema валидация `load_profile` и `project`. | `extra="forbid"` там, где схема финализирована. |
| **Mini-Eval Engine MVP**              | *Static + dynamic @dyn*, переменные из `LoadProfile`, парсер единиц `parse_quantity`, подмена «64Mi» прямо в выражении. | Движок считает CPU/Memory на уровне service. |
| **Requests + Limits**                 | Поддержка `limits`, отдельные агрегаты `totals.requests` и `totals.limits`. | Отсутствие limits не ломает схему. |
| **depends_on граф**                   | DFS-обход Technical → Generic → Infra; кеш `visited` исключает двойной счёт. | `infra.capacity` вычисляется, но не аггрегируется в CPU/RAM. |
| **Мультизонность**                    | Расчёт для всех `zones` в `Project`; итоговый JSON `{ zones: {..}, totals: .. }`. | Для каждой зоны — собственный `Interpreter` с переменными. |
| **Unit-тесты + фикстуры**             | Golden JSON для mini-Blueprint, тест графа depend-on, тест multizone. | Маркер `@pytest.mark.unit`. |
| **Tooling & Dev-Env**                 | `ruff`, `black`, `pre-commit`, pin `click==8.1.7`. | CI пока запускает `pytest` руками (см. «Планируется»). |
| **JSON-Schema для ResourceProfile**   | ➊ Вынесли определение профиля в `resource_profile.schema.json`.<br>➋ Обновили `blueprint.schema.json` — ссылки через `$ref` на новый файл, удалили старые `definitions.Resource*`.<br>➌ В `Blueprint.parse_file()` добавлена jsonschema-валидация каждого профиля; заведён unit-тест «invalid\_profile».                                                            | Единая точка правды для CPU/RAM-шаблонов, нет дублирования схем. Профили проверяются сразу при парсинге, что ловит ошибки до запуска расчёта.                                                               |
| **Полные модели Pydantic**            | ➊ Подняли `datamodel-code-generator 0.31.2` (поддержка Pydantic v2).<br>➋ Скрипт `scripts/gen_models.sh` генерирует классы из всех JSON-Schema (`*_gen.py`).<br>➌ Добавлены тонкие обёртки `LoadProfile`, `Project/Zone`, `Blueprint` c методами `parse_file` и доп-валидацией.<br>➍ CI-шаг проверяет, что автоген в репозитории актуален (`git diff --exit-code`). | Теперь схемы и модели синхронизированы автоматически; внешнее API (unit-тесты, CLI) не менялось. Ошибки несовместимости (`regex`, `__root__`) решены за счёт свежей версии генератора и inheritance-подхода. |
| **Unit-converter 2.0**                | ➊ Расширен `units.py`: поддержка Gi/Ti + десятичные KB/MB/GB/TB и IOPS `NNN/s`.<br>➋ Функция `format_bytes()` выводит объёмы обратно в Mi / Gi / Ti.<br>➌ Реализован новый регэксп и таблица множителей; старые единицы не затронуты.<br>➍ Добавлен юнит-тест `test_units_converter.py`.        | Конвертация покрывает все нужные суффиксы, отчёты XLSX/PDF получают человекочитаемые значения; изменения не ломают существующий код.     |
| **Zone-multiplier**                   | ➊ В `project.schema.json` у `Zone` добавлено поле `factor` (float ≥1, default = 1).<br>➋ Перегенерированы модели (`Zone.factor`).<br>➌ В `MiniEvalEngine` внедрён метод `_scale_zone()` — умножает requests/limits и infra-capacity на коэффициент.<br>➍ Создан тест `test_zone_multiplier.py`. | Теперь одним параметром можно смоделировать Prod-2, DR-site и т.п.; при `factor: 1` ведёт себя как раньше, полная обратная совместимость. |
| **Aggregated infra sizing**           | • Добавлен сбор `infra_totals` в `MiniEvalEngine.run()` - агрегирует `capacity` одинаковых `infra_dependencies` по всем зонам.<br>• Расширён `SizingResult` и обновлены юнит-тесты (проверка суммарного `storage_gb` для PostgreSQL).                                                                                                     | Реализовано точно по плану; использован `defaultdict` для лаконичного сложения, API назад-совместим (добавилось новое поле). |
| **SizingResult schema & model**       | • Создан JSON-Schema `sizing_result.schema.json`.<br>• Генерация `sizing_result_gen.py` через `datamodel-code-generator` добавлена в `scripts/gen_models.py`.<br>• Введён обёрточный класс `SizingResult` с доп-валидацией схемы.<br>• `MiniEvalEngine.run()` теперь возвращает типизированный объект; все юнит-тесты и CLI адаптированы. | Выполнено без отклонений; благодаря строгой модели ловим структурные ошибки ранним CI.                                      |
| **Cross-team overrides audit**        | • Проверка коллизий имён в `BlueprintIndex`.<br>• Первый найденный объект маркируется `origin`, последующие получают `override: true`; путь-источник сохраняется.<br>• При расчёте `MiniEvalEngine` добавляет предупреждение в `SizingResult.messages`, CLI выводит жёлтый лог-стрим.<br>• Юнит-тест `test_overrides_warning` покрывает сценарий. | Реализовано внутри того же прохода DFS, поэтому не влияет на перфоманс; предупреждения доступны как в JSON-API, так и в stdout. Расчётные цифры остаются без изменений. |
| **Док-пример / examples**             | • Создан каталог `examples/`: `acme.project.yaml`, `acme.result.json`, `acme_cli_output.txt`, `regen_result.sh`.<br>• Подробный `examples/README.md` (walk-through «3 команды»).<br>• Ссылки добавлены в корневой README и `docs/architecture_overview.md`; nav-пункт MkDocs.                                                                     | Пример воспроизводится одной командой; заранее сгенерированный `result.json` валидируется схемой в CI; |


---

## Что **планируется к реализации** (веха **v0.5 → v0.6**)

| Приоритет | Блок                            | Конкретные таски | Зачем / ценность |
|-----------|---------------------------------|------------------|------------------|
| **P2**    | **pre-commit расширение**       | Добавить `mypy --strict`, `pytest -m unit`. | Единый локальный барьер качества. |
| **P2**    | **GitHub Action CI**            | Workflow `core-model.yml`: `ruff`, `black --check`, `pytest --cov`, публиковать HTML-coverage в Job Artifacts. | Надёжный «красный/зелёный» при любом PR. |

> ℹ️ Приоритеты:  
> **P0** – критично к ближайшему релизу (Sprint x).  
> **P1** – важно к «твёрдому» окончанию релиза.  
> **P2** – улучшения, делаем при свободном слоте.

---
