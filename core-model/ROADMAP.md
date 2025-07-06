# PRISM **Core-Model** – Roadmap  

> **Ревизия:** 06 июл 2025 → **обновлено: 06 июл 2025 (вечер)**  
> Файл ведётся внутри каталога `core-model` и обновляется после каждой итерации: строки из «Планируется» переносятся в «Сделано», при необходимости добавляются новые задачи.

---

## Что **уже сделано** (v0.2-alpha, Sprint 0 – 3)

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

---

## Что **планируется к реализации** (веха **v0.3 → v0.4**)

| Приоритет | Блок | Конкретные таски | Зачем / ценность |
|-----------|------|------------------|------------------|
| **P0**    | **Полные модели Pydantic** | ➊ Сгенерировать модели из `blueprint.schema.json` (`datamodel-code-generator`).<br>➋ Включить `extra="forbid"`. | Снижает риск опечаток в DSL. |
| **P0**    | **Unit-converter 2.0** | Поддержка `Gi`, `Ti`, `MB`, IOPS «/s»; обратный рендер bytes → `Mi/Gi`. | Корректный вывод в XLSX/PDF. |
| **P0**    | **Zone-multiplier** | В `Zone` добавить `factor` (int/float). При расчёте умножать result каждого zone. | Легко моделировать Prod-2, DR-site. |
| **P1**    | **Cross-team overrides audit** | При коллизии имён в разных Blueprint-ах маркировать `override` + выводить warning в JSON. | Прозрачность для архитекторов. |
| **P1**    | **Док-пример / examples** | Папка `examples/`: `acme.project.yaml`, итог `acme.result.json`, скрин CLI-вывода. | Быстрый smoke-тест и обучающий материал для новичков. |
| **P2**    | **pre-commit расширение** | Добавить `mypy --strict`, `pytest -m unit`. | Единый локальный барьер качества. |
| **P2**    | **Aggregated infra sizing** | Кубик: суммировать одинаковые infra-типы по зонам (PostgreSQL total GB, Kafka partitions). | Полезно для IaaS-/DBA-команд. |
| **P2**    | **JSON-Schema для ResourceProfile** | Вынести `resource_profiles` в отдельную схему + lint на CI. | Единая валидация для всех команд. |
| **P2**    | **GitHub Action CI** | Workflow `core-model.yml`: `ruff`, `black --check`, `pytest --cov`, публиковать HTML-coverage в Job Artifacts. | Надёжный «красный/зелёный» при любом PR. |

> ℹ️ Приоритеты:  
> **P0** – критично к ближайшему релизу (Sprint 4).  
> **P1** – важно к «твёрдому» v0.3… v0.4.  
> **P2** – улучшения, делаем при свободном слоте.

---
