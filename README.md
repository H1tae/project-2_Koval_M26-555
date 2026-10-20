# Primitive DB

## Управление таблицами

Запуск программы:

```bash
uv run database
```

Доступные команды:

```text
create_table <имя_таблицы> <столбец1:тип> <столбец2:тип> ...
list_tables
drop_table <имя_таблицы>
help
exit
```

Поддерживаемые типы данных: `int`, `str`, `bool`.
