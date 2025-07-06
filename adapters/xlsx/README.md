# **PRISM XLSX-Adapter**

> Подмодуль генерации **человекочитаемых отчётов** в формате Microsoft Excel
> (часть уровня **Report/Export** в общей архитектуре PRISM).

---

## 1 Назначение

* Принимает **`SizingResult`** (выход `core-model`) + опционально `Project`.
* Формирует многостраничный XLSX-файл:

  * «Totals» — суммарные CPU / RAM / Storage по зонам.
  * «Services» — Application (3A) / Generic (3B) сервисы.
  * «Infrastructure» — PostgreSQL, Kafka, S3 и др.
* Используется:

  * **CLI** → `prism-cli report project.json --xlsx`.
  * **Spring Service** → REST `GET /reports/{id}?type=xlsx`.
  * **Batch-job** → импорт `bims.prism.adapters.xlsx.build_report`.

---

## 2 Быстрый старт (локальная разработка)

```bash
# 1. Клонируем монорепу и активируем venv
git clone https://github.com/bims/prism.git
cd prism
python -m venv .venv && source .venv/bin/activate

# 2. Ставим зависимости адаптера
pip install -r adapters/xlsx/requirements.txt -r adapters/xlsx/requirements_dev.txt

# 3. Smoke-проверка
pytest adapters/xlsx -q             # 1 тест OK

cd adapters/xlsx/src
python -m bims.prism.adapters.xlsx.cli    # создаст report.xlsx
open report.xlsx                           # в любой Excel-совместимой программе
```

---

## 3 Структура каталога `adapters/xlsx`

```text
adapters/xlsx/
├─ src/
│  └─ bims/prism/adapters/xlsx/
│      ├─ __init__.py        # public facade build_report()
│      ├─ builder.py         # XlsxAdapter (реальный рендер)
│      ├─ cli.py             # опц. CLI для локальных вызовов
│      └─ templates/         # Jinja-Excel XML, стили
├─ tests/
│  ├─ unit/                  # fast pytest tests
│  └─ integration/           # long-running, snapshot diff
├─ requirements.txt          # runtime deps (openpyxl, pandas)
├─ requirements_dev.txt      # pytest, ruff, black, snapshot
├─ pytest.ini                # markers unit / integration
└─ README.md                 ← **этот файл**
```

---

## 4 Публичный API

```python
from bims.prism.adapters.xlsx import build_report

xlsx_bytes: bytes = build_report(
    sizing_result_obj,        # bims.prism.models.SizingResult
    theme="default"
)
with open("sizing.xlsx", "wb") as fh:
    fh.write(xlsx_bytes)
```

*В будущем функция будет расширена параметрами `lang` и `level` (VM / HW).*

---

## 5 Тестирование

| Команда                       | Что проверяет                                |
| ----------------------------- | -------------------------------------------- |
| `ruff adapters-xlsx`          | стиль и импорт-сорты (корп. pre-commit)      |
| `black --check adapters-xlsx` | форматирование PEP 8                         |
| `pytest -m unit`              | быстро (<1 с) — smoke / pure-python          |
| `pytest -m integration`       | snapshot XLSX-файлов → байтовая стабильность |

> Snapshot-тесты используют `pytest-snapshot`.
> Для PDF-основы в другом провайдере сравнение выполняется через `pdf2image`.

---

## 6 Разработка

### 6.1 Шаблоны

* **Jinja-Excel** (`templates/*.xml.j2`) — прямой рендер XML-частей XLSX.
* Использовать `{{ cell("A1") }}` helper-макро (см. `builder.py`).

### 6.2 Локализация

| Язык | Файл                        |
| ---- | --------------------------- |
| RU   | `locales/ru/LC_MESSAGES.po` |
| EN   | `locales/en/LC_MESSAGES.po` |

Переключатель `lang` будет добавлен в версии 0.5 (см. Roadmap).

### 6.3 Стиль

Все цвета / шрифты вынесены в `templates/theme.yaml`.
Новые темы — отдельный YAML + CSS-palette, PR с тегом `feat(theme)`.

---

## 7 CI / CD

* **Workflow:** `.github/workflows/xlsx-adapter.yml`

  * lint → format-check → pytest → upload artefact `report.xlsx` (для diff).
* **Версионирование:** SemVer, теги `xlsx-v0.x.y`.
* **Публикация образа:** не требуется (Pure-Python), идёт как часть основного Docker-слоя CLI.

---

## 8 Дорожная карта

Детальный план — `adapters/xlsx/ROADMAP.md`.

Кратко:

* **0.1** – skeleton (этот PR).
* **0.2** – лист «Totals».
* **0.3** – лист «Services».
* …
* **1.0** – релиз для внешних тендеров (см. Roadmap).

---

## 9 FAQ

| Вопрос                                    | Ответ                                                                         |
| ----------------------------------------- | ----------------------------------------------------------------------------- |
| **Почему openpyxl, а не xlsxwriter?**     | Нужен read-modify (стили, условное форматирование), что проще через openpyxl. |
| **Можно ли подключить LibreOffice Calc?** | Да, XLSX-файл совместим; в Roadmap есть задача на ODS-экспорт.                |
| **Как добавить новый столбец?**           | Изменить Jinja-шаблон и `builder.py`, написать snapshot-тест.                 |

---
