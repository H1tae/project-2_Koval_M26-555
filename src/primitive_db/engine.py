import shlex

import prompt
from prettytable import PrettyTable

from primitive_db.constants import META_FILE, PYTHON_TYPES
from primitive_db.core import (
    create_table,
    delete,
    drop_table,
    insert,
    list_tables,
    select,
    update,
)
from primitive_db.parser import parse_set_clause, parse_values, parse_where_clause
from primitive_db.utils import (
    load_metadata,
    load_table_data,
    save_metadata,
    save_table_data,
)


def print_help():
    """Выводит справку по доступным командам."""
    print("\n***Управление таблицами***")
    print(
        "<command> create_table <имя_таблицы> "
        "<столбец1:тип> <столбец2:тип> .. - создать таблицу"
    )
    print("<command> list_tables - показать список всех таблиц")
    print("<command> drop_table <имя_таблицы> - удалить таблицу")
    print("\n***Операции с данными***")
    print(
        "<command> insert into <имя_таблицы> values "
        "(<значение1>, <значение2>, ...) - создать запись"
    )
    print(
        "<command> select from <имя_таблицы> where "
        "<столбец> = <значение> - прочитать записи по условию"
    )
    print("<command> select from <имя_таблицы> - прочитать все записи")
    print(
        "<command> update <имя_таблицы> set <столбец> = "
        "<значение> where <столбец> = <значение> - обновить запись"
    )
    print(
        "<command> delete from <имя_таблицы> where "
        "<столбец> = <значение> - удалить запись"
    )
    print("<command> info <имя_таблицы> - вывести информацию о таблице")
    print("\nОбщие команды:")
    print("<command> exit - выход из программы")
    print("<command> help - справочная информация\n")


def _column_types(metadata, table_name):
    """Возвращает типы столбцов указанной таблицы."""
    if table_name not in metadata:
        raise KeyError(table_name)
    return {
        column_name: type_name
        for column_name, type_name in (
            column.split(":", 1) for column in metadata[table_name]
        )
    }


def _validate_clause(metadata, table_name, clause):
    """Проверяет имена столбцов и типы значений условия."""
    column_types = _column_types(metadata, table_name)
    for column_name, value in clause.items():
        if column_name not in column_types:
            raise ValueError(column_name)
        if type(value) is not PYTHON_TYPES[column_types[column_name]]:
            raise ValueError(value)


def _print_records(metadata, table_name, records):
    """Выводит записи таблицы с помощью PrettyTable."""
    columns = [column.split(":", 1)[0] for column in metadata[table_name]]
    result_table = PrettyTable()
    result_table.field_names = columns
    for record in records:
        result_table.add_row([record[column] for column in columns])
    print(result_table)


def _handle_create_table(args, user_input, metadata):
    """Обрабатывает команду создания таблицы."""
    if len(args) < 3:
        raise ValueError(user_input)
    table_name = args[1]
    table_existed = table_name in metadata
    updated_metadata = create_table(metadata, table_name, args[2:])
    if (
        updated_metadata is not None
        and not table_existed
        and table_name in updated_metadata
    ):
        save_metadata(META_FILE, updated_metadata)


def _handle_drop_table(args, user_input, metadata):
    """Обрабатывает команду удаления таблицы."""
    if len(args) != 2:
        raise ValueError(user_input)
    table_name = args[1]
    table_existed = table_name in metadata
    updated_metadata = drop_table(metadata, table_name)
    if (
        updated_metadata is not None
        and table_existed
        and table_name not in updated_metadata
    ):
        save_metadata(META_FILE, updated_metadata)


def _handle_insert(args, user_input, metadata):
    """Обрабатывает команду добавления записи."""
    if len(args) < 5 or args[1] != "into" or args[3] != "values":
        raise ValueError(user_input)

    table_name = args[2]
    _, separator, values_text = user_input.partition(" values ")
    if not separator:
        raise ValueError(user_input)

    values = parse_values(values_text)
    updated_data = insert(metadata, table_name, values)
    if updated_data is None:
        return
    save_table_data(table_name, updated_data)
    record_id = updated_data[-1]["ID"]
    print(f'Запись с ID={record_id} успешно добавлена в таблицу "{table_name}".')


def _handle_select(args, user_input, metadata):
    """Обрабатывает команду чтения записей."""
    if len(args) < 3 or args[1] != "from":
        raise ValueError(user_input)

    table_name = args[2]
    _column_types(metadata, table_name)
    where_clause = None
    if len(args) > 3:
        if args[3] != "where":
            raise ValueError(user_input)
        _, separator, where_text = user_input.partition(" where ")
        if not separator:
            raise ValueError(user_input)
        where_clause = parse_where_clause(where_text)
        _validate_clause(metadata, table_name, where_clause)

    table_data = load_table_data(table_name)
    records = select(table_data, where_clause)
    _print_records(metadata, table_name, records)


def _handle_update(args, user_input, metadata):
    """Обрабатывает команду обновления записей."""
    if len(args) < 8 or args[2] != "set" or "where" not in args:
        raise ValueError(user_input)

    table_name = args[1]
    before_where, where_separator, where_text = user_input.partition(" where ")
    _, set_separator, set_text = before_where.partition(" set ")
    if not where_separator or not set_separator:
        raise ValueError(user_input)

    set_clause = parse_set_clause(set_text)
    where_clause = parse_where_clause(where_text)
    _validate_clause(metadata, table_name, set_clause)
    _validate_clause(metadata, table_name, where_clause)

    table_data = load_table_data(table_name)
    record_ids = [record["ID"] for record in select(table_data, where_clause)]
    updated_data = update(table_data, set_clause, where_clause)
    save_table_data(table_name, updated_data)
    for record_id in record_ids:
        print(f'Запись с ID={record_id} в таблице "{table_name}" успешно обновлена.')


def _handle_delete(args, user_input, metadata):
    """Обрабатывает команду удаления записей."""
    if len(args) < 7 or args[1] != "from" or args[3] != "where":
        raise ValueError(user_input)

    table_name = args[2]
    _, separator, where_text = user_input.partition(" where ")
    if not separator:
        raise ValueError(user_input)
    where_clause = parse_where_clause(where_text)
    _validate_clause(metadata, table_name, where_clause)

    table_data = load_table_data(table_name)
    record_ids = [record["ID"] for record in select(table_data, where_clause)]
    updated_data = delete(table_data, where_clause)
    if updated_data is None:
        return
    save_table_data(table_name, updated_data)
    for record_id in record_ids:
        print(f'Запись с ID={record_id} успешно удалена из таблицы "{table_name}".')


def _handle_info(args, user_input, metadata):
    """Обрабатывает команду вывода информации о таблице."""
    if len(args) != 2:
        raise ValueError(user_input)
    table_name = args[1]
    _column_types(metadata, table_name)
    table_data = load_table_data(table_name)
    print(f"Таблица: {table_name}")
    print(f"Столбцы: {', '.join(metadata[table_name])}")
    print(f"Количество записей: {len(table_data)}")


def run():
    """Запускает основной цикл управления базой данных."""
    print_help()

    while True:
        metadata = load_metadata(META_FILE)
        user_input = prompt.string(">>>Введите команду: ")

        try:
            args = shlex.split(user_input)
            if not args:
                raise ValueError(user_input)

            command = args[0]
            if command == "exit":
                return
            if command == "help":
                print_help()
            elif command == "create_table":
                _handle_create_table(args, user_input, metadata)
            elif command == "drop_table":
                _handle_drop_table(args, user_input, metadata)
            elif command == "list_tables":
                if len(args) != 1:
                    raise ValueError(user_input)
                list_tables(metadata)
            elif command == "insert":
                _handle_insert(args, user_input, metadata)
            elif command == "select":
                _handle_select(args, user_input, metadata)
            elif command == "update":
                _handle_update(args, user_input, metadata)
            elif command == "delete":
                _handle_delete(args, user_input, metadata)
            elif command == "info":
                _handle_info(args, user_input, metadata)
            else:
                print(f"Функции {command} нет. Попробуйте снова.")
        except KeyError as error:
            print(f'Ошибка: Таблица "{error.args[0]}" не существует.')
        except ValueError as error:
            print(f"Некорректное значение: {error}. Попробуйте снова.")
