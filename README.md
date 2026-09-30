# booking-miniapp

Короткое описание: что делает проект и зачем.

## Запуск

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # заполнить своими значениями
booking-miniapp           # или: python -m booking_miniapp
```

## Тесты и линтер

```bash
pytest
ruff check .
```

## Структура

```
src/booking_miniapp/   код
tests/              тесты
```
