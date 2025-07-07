# **PRISM** — Универсальный инструмент сайзинга и моделирования инфраструктуры

> **PRISM** = *Platform Resource & Infrastructure Sizing Model*

---

## 1  Назначение

`PRISM` — это **расширяемый набор инструментов**, который превращает бизнес‑входные данные (кол‑во пользователей, объёмы данных, требования к отказоустойчивости) в готовые документы сайзинга (XLSX, PDF/HTML) под любую среду — от одной VM до геораспределённого облака.

> **Кому полезно?**
> • *Pre‑sales / PM* — формируют тендерную документацию за минуты.
> • *Менеджеры заказчика* — подбирают параметры в self‑service UI.
> • *DevOps / SRE* — подключают YAML‑модель прямо в IaC‑конвейер.

---

## Репозиторий: обзор

```
.
├─ common/               # prism-common — схемы + утилиты (Python)
├─ core-model/           # prism-core   — движок расчёта (Python)
├─ adapters/
│   ├─ xlsx/             # prism-adapters-xlsx   — Excel-отчёты (Python)
│   └─ report/           # prism-adapters-report — PDF/HTML-отчёты (Python)
├─ service/              # Spring Boot REST-API + gRPC к ядру
├─ spa/                  # React SPA (Ant Design, i18n)
├─ infra/                # docker-compose, Helm-chart, GitHub Actions
└─ docs/                 # MkDocs site, ADR, diagrams
```

*Быстрый тех-дайджест см. в README внутри каждого модуля:*

| Компонент             | README                                   | Стек (core)               |
|-----------------------|------------------------------------------| ------------------------- |
| **Calculations**      | [core-model](core-model/README.md)       | Python 3.12 + Pydantic v2 |
| **Excel-reports**     | [adapters/xlsx](adapters/xlsx/README.md) | Python 3.12 + openpyxl    |
| **Shared schemas**    | —                                        | —                         |
| **Admin WEB Service** | [service](service/README.md)             | Java 21 + Spring Boot 3   |
| **Web-SPA**           | [spa](spa/README.md)                     | TypeScript 5 + React 18   |

---

## Как попробовать за 5 минут

```bash
git clone https://github.com/bims/prism.git
cd prism
python -m venv .venv && source .venv/bin/activate

# 1) расчёт
pip install -e common -e core-model           # только ядро
python -m bims.prism.cli calculate \
   examples/acme.project.yaml examples/blueprints > result.json

# 2) отчёт
pip install -e adapters/xlsx                  # ставим нужный адаптер
python -m bims.prism.adapters.xlsx.cli result.json -o acme.xlsx
open acme.xlsx
```

*(Полный dev-stack — см. инструкции в `infra/` и модульных README.)*

---

## Документация

* [Бизнес‑введение](docs/business_intro.md)
* [Лесенка уровней и глоссарий PRISM](docs/layers_and_glossary.md)
* [Архитектурный обзор](docs/architecture_overview.md)
* [Дорожная карта](docs/roadmap.md)
* [Blueprint DSL](docs/blueprint_dsl.md)
* [Отчётные провайдеры](docs/adapters_report_architecture.md)

---

## Лицензия

PRISM распространяется под **Apache 2.0** — см. файл [`LICENSE`](LICENSE).
