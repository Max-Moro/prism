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

## 2  Структура репозитория

```
.
├── adapters/           # Генераторы XLSX и PDF/HTML (Python)
│   ├── xlsx/           # openpyxl‑реализация
│   └── report/         # Jinja2 + WeasyPrint шаблоны
├── core-model/         # Движок формул (Python, Pydantic)
├── service/            # Spring Boot REST API для админ‑панели
├── spi/                # React + TypeScript SPA (Ant Design)
├── infra/              # Dev/CI окружение (docker‑compose, helm)
└── docs/               # MkDocs, ADR, диаграммы архитектуры
```

| Модуль              | Язык / Рантайм | Основные зависимости              |
| ------------------- | -------------- | --------------------------------- |
| **core-model**      | Python 3.12    | Pydantic v2, PyYAML               |
| **adapters/xlsx**   | Python 3.12    | pandas, openpyxl                  |
| **adapters/report** | Python 3.12    | Jinja2, WeasyPrint                |
| **service**         | Java 21        | Spring Boot 3, JPA, PostgreSQL 16 |
| **spi**             | TypeScript 5   | React 18, MobX 6, Ant Design 5    |

### Примеры namespace

| Язык                   | Пример                                    |
| ---------------------- | ----------------------------------------- |
| **Java (Spring Boot)** | `package bims.prism.core;`                |
| **Python**             | `from prism.model import CustomerProfile` |

---

## 3  Быстрый старт (локальная разработка)

1. **Клонирование**

   ```bash
   git clone https://github.com/bims/prism.git
   cd prism
   ```
2. **Требования**: Docker ≥ 24, Python 3.12, Node 20, Java 21.
3. **Запуск всех сервисов**:

   ```bash
   docker compose -f infra/docker-compose.yaml up --build
   # core-model API → http://localhost:8000/health
   # admin service  → http://localhost:8080/actuator/health
   # SPA            → http://localhost:5173
   ```
4. **Запуск unit‑тестов**:

   ```bash
   make test           # pytest + mvn + vitest
   ```

---

## 4  Рабочий процесс

1. **Ветки** — `main` (защищённая) ↔ feature‑ветки (`feat/*`, `fix/*`).
2. **Коммиты** — Conventional Commits + автогенерация changelog.
3. **CI** — GitHub Actions (`lint`, `test`, `build`, `e2e`, `docker-push`).
4. **Трекер задач** — GitHub Projects (Kanban).
5. **Code review** — PR + обязательные статус‑чеки.

---

## 5  Дополнительная документация

* [Бизнес‑введение](docs/business_intro.md)
* [Архитектурный обзор](docs/architecture_overview.md)
* [Дорожная карта](docs/roadmap.md)

---

## 6  Лицензия

Проект распространяется под лицензией **Apache 2.0**. Подробности в файле `LICENSE`.
