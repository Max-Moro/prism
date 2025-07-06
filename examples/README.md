# Walk-through: «PRISM за 3 минуты»

*Мини-гайд для новичка: как прогнать готовый пример и получить валидный JSON-сайзинг.*

---

## 1 · Клонируем репозиторий и ставим зависимости

```bash
git clone https://github.com/bims/prism.git
cd prism
pip install -r core-model/requirements.txt
```

> Или поднимите всё через Docker-Compose (`infra/docker-compose.yaml`) —  
> пример не требует сервисов, но так вы сразу увидите полноценное окружение.

---

## 2 · Запускаем smoke-тест

```bash
cd core-model/src
python -m bims.prism.cli \
    ../../examples/acme.project.yaml \
    ../../examples/blueprints/ \
  | jq '.totals'
```

Ожидаемый вывод (усечён — только агрегаты):

```json
{
  "requests": { "cpu": 0.192, "memory": 539090176 },
  "limits":   { "cpu": 0.576, "memory": 1023410176 }
}
```

---

## 3 · Проверяем «zero-diff»

Файл `examples/acme.result.json` хранит канонический результат.  
Сравните его с текущим расчётом — убедимся, что формулы не сломаны:

```bash
diff -u <(jq -S . ../../examples/acme.result.json) \
       <(python -m bims.prism.cli ../../examples/acme.project.yaml ../../examples/blueprints/ | jq -S .)
```

Если команда ничего не вывела — конфигурация стабильна.

---

## 4 · Поиграемся с параметрами

Откройте `examples/acme.project.yaml` и измените, например,  
`online_users` в зоне **Prod** с `2500` → `5000`. Перезапустите расчёт:

```bash
python -m bims.prism.cli ../../examples/acme.project.yaml ../../blueprints/ \
  | jq '.zones.Prod.totals.requests'
```

CPU и память вырастут ровно в два раза — проверьте!

---

## 5 · Что дальше

* Генерируйте **XLSX** или **PDF** через модули adapters.  
* Подключите JSON-вывод к своему Terraform-pipeline.  
* Добавьте собственный Blueprint и посмотрите, как изменится граф зависимостей.

