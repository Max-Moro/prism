# Архитектура PRISM (верхний уровень)

> **Версия 0.2 — учтены уточнения 05 июл 2025**

---

## 1. Главные требования проекта и способы их удовлетворения

| Категория                        | Формулировка                                                                                                            | Как удовлетворяем                                                                                                                   |
| -------------------------------- |-------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------|
| **Модульность**                  | Управление **бизнес‑модулями** на уровне PM; автоматическая активация требуемых **технических** и **generic‑сервисов**. | YAML‑конфиг зависимостей (`module‑graph.yaml`), поддерживаемый архитекторами. Core‑Model строит граф и включает только нужные узлы. |
| **Много‑зонность**               | Заказчик может иметь Prod‑1, Prod‑2, Pre‑Prod, Test, DR и пр.                                                           | Zone‑объекты + коэффициенты умножения; UI позволяет добавлять зоны.                                                                 |
| **Low coupling / High cohesion** | Изоляция контуров: Core‑Model ≠ Service ≠ SPA.                                                                          | *gRPC* только между Service ⇆ Core‑Model; *OpenAPI* между SPI ⇆ Service.                                                            |
| **CLI‑режим**                    | Возможность локально запустить расчёт без сервера.                                                                      | `prism-cli calculate acme.yaml --xlsx` — запускает Core‑Model как lib.                                                              |
| **Прослеживаемость**             | Audit‑trail входных YAML и формул.                                                                                      | Храним в Git; SHA входа/кода пишем в отчёт.                                                                                         |
| **Self‑service**                 | Менеджер заказчика «крутит ручки» сам.                                                                                  | Web‑SPA + live‑валидация + on‑demand отчёт.                                                                                         |
| **Локализация UI**               | RU по умолчанию, EN «по кнопке».                                                                                        | i18n в SPA (react‑i18next); фразы вне кода.                                                                                         |
| **Интеграция с IaC**             | Terraform‑provider (backlog).                                                                                           | Отложено в Roadmap 1.1; реализация — собственный provider на Go + OpenAPI‑generated client.                                         |
| **Security / RBAC**              | Роли PM, customer‑manager, SRE.                                                                                         | Keycloak + spring‑security.                                                                                                         |

---

## 2. Разделение ответственности и потоки

```
┌───────────────┐     gRPC (async)     ┌──────────────┐
│ Core‑Model    │ <───────────────────>│ Service API  │
│  (Python)     │                      │  (Spring)    │
└───────────────┘                      └──────────────┘
        ▲                                     ▲
  CLI   │                                     │ OpenAPI 3
        │                                     │
┌───────┴───────┐                        ┌────┴────────┐
│ Adapters      │                        │ SPA (React)│
│  XLSX/PDF     │                        │            │
└───────────────┘                        └────────────┘
```

* **Core‑Model** — движок расчётов; стартует либо как gRPC‑server (`uvicorn prism.api.grpc:app`), либо как `prism-cli`.
* **Service** — orchestration: аутентификация, CRUD, история отчётов, вызов Core‑Model по gRPC.
* **Adapters** — либы, импортируют Core‑Model напрямую (в batch‑джобах) или вызывают gRPC.
* **SPA** — фронт, общается с Service REST‑ом.

---

## 3. Технологии интеграции

| Поток                | Технология                                   | Формат             | Причина                                             |
|----------------------| -------------------------------------------- | ------------------ | --------------------------------------------------- |
| Service ⇆ Core‑Model | **gRPC** (protobuf)                          | Protobuf           | Высокая производительность, строгие контракты.      |
| CLI → Core‑Model     | Вызов Python‑API                             | YAML in / JSON out | Удобно запускать в IDE или скриптом.                |
| SPA ⇆ Service        | REST (OpenAPI 3)                             | JSON               | Широкая поддержка axios / AntD, автоген TS‑клиента. |
| CI Artefacts         | Docker Registry                              | OCI images         | Единая цепочка доставки.                            |
| IaC Export           | JSON файл → Terraform provider (Roadmap 1.1) | HCL/JSON           | Позволит DevOps автоматизировать развёртывание.     |

---

## 4. Фреймворки и технологии по модулям

| Модуль              | Стек                                                                                                    | Почему выбран                                                        |
|---------------------| ------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| **core-model**      | Python 3.12, Pydantic v2, Typer CLI, **grpcio**, protobuf‑gen, pandas                                   | Python быстр для формул; gRPC‑stub‑код генерируется; CLI на Typer.   |
| **adapters/xlsx**   | pandas, openpyxl, Jinja‑Excel, pytest‑snapshot                                                          | Табличные преобразования + snapshot‑тесты.                           |
| **adapters/report** | Jinja2, WeasyPrint                                                                                      | PDF без LaTeX, легко контейнеризуется.                               |
| **service**         | Java 21, Spring Boot 3.3, grpc‑spring‑boot‑starter, springdoc‑openapi, MapStruct, Flyway, PostgreSQL 16 | Корпоративный стандарт, gRPC‑integration, удобный OpenAPI генератор. |
| **spa**             | React 18, Vite, TypeScript 5, MobX 6, Ant Design 5, react‑i18next, openapi‑typescript‑codegen           | Быстрый HMR, AntD ускоряет CRUD, i18n поддержка.                     |
| **auth**            | Keycloak 24, JWT cookies, spring‑security                                                               | OIDC, fine‑grained roles.                                            |

---

## 5. Концепции домена и модель данных

### 5.1 Типы сущностей

| Сущность                     | Описание                                                                                                |
| ---------------------------- | ------------------------------------------------------------------------------------------------------- |
| **BusinessModule**           | Логический функциональный блок, понятный заказчику («Инспекции», «Картография», «Управление стройкой»). |
| **TechnicalService**         | Реальный исполняемый сервис/контейнер. Может обслуживать несколько бизнес‑модулей.                      |
| **GenericService**           | Общесистемный сервис (ЭЦП, уведомления, СЗИ), может требоваться множеству TechnicalService.             |
| **InfrastructureDependency** | Внешняя инфраструктура (PostgreSQL, Kafka, S3/FS, ClickHouse).                                          |

**Правила зависимостей**

```
BusinessModule ──> {TechnicalService+} ──> {GenericService*} ──> {InfrastructureDependency*}
```

`<team_name>.blueprint.yaml` хранит эти связи. Core‑Model строит transitively‑closed набор сервисов и инфраструктуры для расчёта.

### 5.2 ER‑модель

Упрощенная ER‑модель.

```
Customer(1) ── (N) Project                        ──                    (N) Zone ── (N) Report
                      │                                                     |
                      └──(N) EnabledBusinessModule                          └──(1) Load Profile
                                  │
                                  └─(N) ResolvedService
                                           │
                                           └─(N) ResolvedGeneric
                                                    └─(N) ResolvedInfra
                                           └─(N) ResolvedInfra
```

---

## 6. Конфигурирование и развёртывание

| Опция             | Детали                                                                                                                                                                                     |
| ----------------- |--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Local Dev**     | `docker‑compose`: PostgreSQL, Core‑Model (gRPC), Service, SPA. CLI запускается локально.                                                                                                   |
| **Kubernetes**    | Helm‑chart `infra/helm/prism`:<br>• Core‑Model Deployment с gRPC health‑probe.<br>• Service Deployment (ingress http + grpc).<br>• SPA как Nginx‑static.<br>Разделяем values для dev/prod. |
| **Feature‑flags** | `values.yaml` переключает профили S3/FS, DMZ‑bridge, managed‑DB.                                                                                                                           |
| **Observability** | Prometheus + Grafana: gRPC interceptors + Spring Actuator metrics.                                                                                                                         |
| **Secrets**       | External Secrets Operator / Vault templates.                                                                                                                                               |

---

### Открытые вопросы / TODO

1. **Terraform provider** — реализовать после v1.0 (Backlog 1.1).
2. **PDF‑подпись** — отложено до версии 1.2.

*Многоязычность RU/EN включена в текущий scope v0.5.*
