# DSL «PRISM Blueprint»

> **Цель** — единообразно описывать (в YAML) цепочку от **BusinessModule → TechnicalService → GenericService → InfrastructureDependency** и связывать её с нагрузочным профилем.
>
> **Аудитория** — тимлиды продуктовых команд и DevOps‑инженеры.

---

## 1. Почему «Blueprint»

*Блупринт* в строительстве — комплект чертежей, по которым возводят здание. Здесь `*.blueprint.yaml` — «чертёж» цифрового продукта: что нужно развернуть и как масштабировать.

`pbp://…` — URL‑схема для внутренних ссылок между элементами Blueprint.

---

## 2. Расклад файлов по командам

```
monolith.blueprint.yaml
core-team.blueprint.yaml
construction-team.blueprint.yaml
slp-team.blueprint.yaml
techmoon-team.blueprint.yaml
```

Каждый файл мержится Core‑Model’ю в единый граф.

---

## 3. Соответствие архитектурным уровням

| Уровень | Элемент Blueprint            | YAML‑ключ            |
| ------- | ---------------------------- | -------------------- |
| 3A      | **BusinessModule**           | `business_modules`   |
| 3A      | **TechnicalService**         | `technical_services` |
| 3B      | **GenericService**           | `generic_services`   |
| 3B      | **InfrastructureDependency** | `infra_dependencies` |
| 2       | **ResourceProfile**          | `resource_profiles`  |

---

## 4. Пример Blueprint (фрагмент)

```yaml
$schema: "https://bims.dev/prism/blueprint.schema.json"
kind: Blueprint
team: core-team
version: 1.0.0   # semver

business_modules:
  inspection:
    title: "Инспекции"
    services: [inspection-api, inspection-worker]
    parameters:
      forms_per_user_per_day: 8
      photo_avg_size_mb: 3

technical_services:
  inspection-api:
    image: registry.bims.dev/inspection-api:{{ semver }}
    resources:
      profile: medium-web            # ссылка на static/dynamic пресет
    capacity:
      cpu: "0.1 + 0.0005 * rps"
      memory: "256Mi + 5Mi * rps_p95"
    depends_on: [postgres-primary, kafka-cluster]

  inspection-worker:
    image: registry.bims.dev/inspection-worker:{{ semver }}
    resources:
      profile: small-bg@dyn          # выбираем динамический профиль
    capacity:
      cpu: "0.05 + 0.002 * jobs_rate"
    depends_on: [kafka-cluster, s3-storage]

generic_services:
  notification:
    image: registry.bims.dev/notify:latest
    resources:
      profile: xsmall-web
    capacity:
      cpu: "0.02 + 0.001 * messages_per_sec"

infra_dependencies:
  postgres-primary:
    type: postgres
    version: "16"
    capacity:
      storage_gb: "5 + 0.01 * structured_data_gb"
  kafka-cluster:
    type: kafka
    capacity:
      partitions: "ceil(rps / 50)"
  s3-storage:
    type: s3
    capacity:
      bucket_gb: "unstructured_data_gb * 1.2"

# === Container Orchestration Layer ===
resource_profiles:
  medium-web:
    static:
      requests: { cpu: "200m", memory: "512Mi" }
      limits:   { cpu: "400m", memory: "1Gi" }
    dynamic:                          # зависит от online_users
      requests:
        cpu:    "0.08  + 0.00008  * online_users"   # cores
        memory: "256Mi + 0.20Mi  * online_users"
      limits:
        cpu:    "0.16  + 0.00016  * online_users"
        memory: "512Mi + 0.30Mi  * online_users"

  small-bg:
    static:
      requests: { cpu: "100m", memory: "256Mi" }
      limits:   { cpu: "300m", memory: "512Mi" }
    dynamic:
      requests:
        cpu:    "0.04 + 0.00004 * online_users"
        memory: "128Mi + 0.10Mi * online_users"
      limits:
        cpu:    "0.12 + 0.00012 * online_users"
        memory: "256Mi + 0.15Mi * online_users"

  xsmall-web:
    static:
      requests: { cpu: "50m",  memory: "128Mi" }
      limits:   { cpu: "150m", memory: "256Mi" }
    dynamic:
      requests:
        cpu:    "0.02 + 0.00002 * online_users"
        memory: "64Mi  + 0.05Mi * online_users"
      limits:
        cpu:    "0.06 + 0.00006 * online_users"
        memory: "128Mi + 0.08Mi * online_users"
```

### Замечания

* **mini‑eval DSL** — все формулы вычисляются движком на базе `asteval` (Python) с белым списком функций (`ceil`, `min`, `max`, арифметика).
* Профиль выбирается указанием `profile: <name>` (статичный) или `profile: <name>@dyn` (динамический).
* **Cross‑team overrides**: любой Blueprint может переопределить `resource_profiles` и `capacity` сервисов, определённых в других файлах (последний «побеждает»). CI‑валидатор маркирует такие случаи тегом `override`.
* Ссылки только на **image**; Helm‑чарты будут генерироваться из Blueprint (planned).

---

## 5. Связь с Load Profile

```yaml
load_profile:
  online_users:         2500
  total_users:          12000
  rps:                  180
  rps_p95:              150
  jobs_rate:            40
  structured_data_gb:   380
  unstructured_data_gb: 520
```

`online_users` подставляется во все `@dyn` профили и формулы capacity.

---

## 6. Процесс расширения Blueprint

1. Создаём `new-team.blueprint.yaml` в ветке `feat/<team>`.
2. CI валидирует JSON Schema + lint формул.
3. Архитектор ревьюит, особенно `override`‑теги.
4. Merge → main — новая версия в semver, Core‑Model подхватывает.

---

## 7. Решённые вопросы

| Вопрос               | Ответ                                                                      |
| -------------------- | -------------------------------------------------------------------------- |
| Versioning           | **semver** для каждого Blueprint.                                          |
| Formula engine       | Встроенный **mini‑eval**.                                                  |
| Cross‑team overrides | Разрешены, фиксируются тегом `override` в отчёте CI.                       |
| Artefacts            | В Blueprint — **только контейнер‑image**; Helm‑чарты будут генерироваться. |
