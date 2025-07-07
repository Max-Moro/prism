# **PRISM XLSX-Adapter**

> Генератор **человекочитаемых Excel-отчётов** (часть уровня *Report/Export*
> экосистемы PRISM). Пакет публикуется отдельно — **`prism-adapters-xlsx`**.

---

## 1 Назначение

* Принимает **`SizingResult`** (JSON-вывод `prism-core calculate …`).

* Формирует многостраничный XLSX:

  | Лист         | Содержимое (MVP 0.3)         |
  | ------------ | ---------------------------- |
  | **Totals**   | CPU / RAM / Storage по зонам |
  | **Services** | Application 3A + Generic 3B  |
  | **Infra**    | PostgreSQL, Kafka, S3 и др.  |

* Точки использования

  * **CLI** → `python -m bims.prism.adapters.xlsx.cli sizing.json -o report.xlsx`
  * **Spring Service** → `GET /reports/{id}?format=xlsx` (под-процесс).
  * **Batch** → `from bims.prism.adapters.xlsx import build_report`.

---

## 2 Быстрый старт (локальная разработка)

```bash
# 0) Клонируем монорепу и активируем venv
git clone https://github.com/bims/prism.git
cd prism
python -m venv .venv && source .venv/bin/activate

# 1) Устанавливаем общие утилиты + адаптер в editable-режиме
pip install -e common               # prism-common  (units, schemas)
pip install -e adapters/xlsx        # prism-adapters-xlsx
# ⬆️  зависимости ядра НЕ подтягиваются

# 2) Smoke-тесты
pytest adapters/xlsx -q             # 2 теста OK

# 3) CLІ‐проверка (генерирует report.xlsx из dummy-данных)
python -m bims.prism.adapters.xlsx.cli examples/sizing_result.sample.json
open report.xlsx                    # Excel / LibreOffice / Numbers
```

> **PyCharm tip:** не помечайте каталоги `src/…` как *Sources* – editable-install
> уже прописывает пути; IDE увидит `bims.prism.adapters.xlsx` автоматически.

---

## 3 Структура каталога

```text
prism-adapters-xlsx/
├─ pyproject.toml                  # wheel prism-adapters-xlsx
├─ src/
│   └─ bims/prism/adapters/xlsx/
│       ├─ __init__.py             # build_report()
│       ├─ builder.py              # XlsxAdapter
│       ├─ cli.py                  # CLI wrapper (subprocess-friendly)
│       └─ templates/
│           ├─ totals.xml.j2
│           └─ …                   # future sheets
├─ tests/
│   ├─ unit/
│   ├─ integration/
│   └─ __snapshots__/
└─ README.md  ← **этот файл**
```

---

## 4 Публичный API (MVP 0.2)

```python
from bims.prism.adapters.xlsx import build_report
import json, pathlib

sizing = json.loads(pathlib.Path("sizing_result.prod.json").read_text())
xlsx_bytes = build_report(sizing, theme="default")

pathlib.Path("sizing.xlsx").write_bytes(xlsx_bytes)
```

*Параметры `lang` и `level` (VM / HW) появятся после v0.5.*

---

## 5 Тестирование

| Команда                               | Проверяет                 |
| ------------------------------------- | ------------------------- |
| `ruff adapters/xlsx`                  | стиль / авто-импорт       |
| `black --check adapters/xlsx`         | формат PEP 8              |
| `pytest -m unit adapters/xlsx`        | fast (<1 с) — pure-python |
| `pytest -m integration adapters/xlsx` | snapshot-diff XLSX-файлов |

> Snapshot-тесты используют **pytest-snapshot**: первый запуск
> `pytest --snapshot-update` создаёт эталон `__snapshots__/totals.xlsx`.

---

## 6 Разработка

### 6.1 Шаблоны

* **Jinja-Excel** (`templates/*.xml.j2`) — рендер XML-частей XLSX напрямую.
* Используйте макросы `cell()`, `style()` из `builder.py` (см. док-строки).

### 6.2 Локализация

| Язык | Файл                        |
| ---- | --------------------------- |
| RU   | `locales/ru/LC_MESSAGES.po` |
| EN   | `locales/en/LC_MESSAGES.po` |

Переключатель `lang` запланирован в версии 0.5 (см. Roadmap).

### 6.3 Темы дизайна

Все цвета / шрифты в `templates/theme.yaml`.
Новый бренд → новый YAML + CSS-palette → PR с тегом `feat(theme)`.

---

## 7 CI

* **Workflow:** `.github/workflows/ci.yml` — общий для `common`, `core`, `xlsx`.
* Шаги: lint → format-check → pytest → upload artefact `report.xlsx` (diff-trace).

---

## 8 Дорожная карта

Смотри `adapters/xlsx/ROADMAP.md`.

| Версия  | Спринты | Ключевая фича         |
| ------- | ------- | --------------------- |
| **0.1** | S-1     | Skeleton (Hello XLSX) |
| **0.2** | S-2     | Лист **Totals**       |
| **0.3** | S-3     | Лист **Services**     |
| …       | …       | …                     |
| **1.0** | S-9/10  | Готовность к тендерам |

---

## 9 FAQ

| Вопрос                                | Ответ                                                                      |
| ------------------------------------- | -------------------------------------------------------------------------- |
| **Почему openpyxl, а не xlsxwriter?** | Нужен read-modify (стили, условное форматирование) — проще через openpyxl. |
| **Совместимо ли с LibreOffice Calc?** | Да, файл открывается напрямую; в Roadmap есть задача на ODS-экспорт.       |
| **Как добавить новый столбец?**       | Изменить Jinja-шаблон и `builder.py`, обновить snapshot-тест.              |

---
