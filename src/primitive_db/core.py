from primitive_db.constants import PYTHON_TYPES, VALID_TYPES
from primitive_db.decorators import (
    confirm_action,
    create_cacher,
    handle_db_errors,
    log_time,
)
from primitive_db.utils import load_table_data

cache_result = create_cacher()


@handle_db_errors
def create_table(metadata, table_name, columns):
    """Создаёт таблицу и добавляет её структуру в метаданные."""
    if table_name in metadata:
        raise ValueError(f'Таблица "{table_name}" уже существует.')

    for column in columns:
        column_parts = column.split(":")
        if (
            len(column_parts) != 2
            or not column_parts[0]
            or column_parts[1] not in VALID_TYPES
        ):
            raise ValueError(column)

    table_columns = ["ID:int", *columns]
    metadata[table_name] = table_columns
    columns_text = ", ".join(table_columns)
    print(
        f'Таблица "{table_name}" успешно создана со столбцами: '
        f"{columns_text}"
    )
    return metadata


@handle_db_errors
@confirm_action("удаление таблицы")
def drop_table(metadata, table_name):
    """Удаляет таблицу из метаданных."""
    if table_name not in metadata:
        raise KeyError(table_name)

    del metadata[table_name]
    print(f'Таблица "{table_name}" успешно удалена.')
    return metadata


def list_tables(metadata):
    """Выводит названия существующих таблиц."""
    for table_name in metadata:
        print(f"- {table_name}")


@handle_db_errors
@log_time
def insert(metadata, table_name, values):
    """Добавляет запись в таблицу и возвращает обновлённые данные."""
    if table_name not in metadata:
        raise KeyError(table_name)

    columns = metadata[table_name][1:]
    if len(values) != len(columns):
        raise ValueError(
            f"ожидалось значений: {len(columns)}, получено: {len(values)}"
        )

    record = {}
    for column_definition, value in zip(columns, values, strict=True):
        column_name, type_name = column_definition.split(":", 1)
        if type(value) is not PYTHON_TYPES[type_name]:
            raise ValueError(
                f'для столбца "{column_name}" ожидается тип {type_name}'
            )
        record[column_name] = value

    table_data = load_table_data(table_name)
    record_ids = [row["ID"] for row in table_data]
    record["ID"] = max(record_ids, default=0) + 1
    record = {"ID": record.pop("ID"), **record}
    return [*table_data, record]


@log_time
def select(table_data, where_clause=None):
    """Возвращает все записи или записи, подходящие под условие."""
    cache_key = (
        tuple(tuple(sorted(record.items())) for record in table_data),
        tuple(sorted((where_clause or {}).items())),
    )

    def get_records():
        if where_clause is None:
            return table_data
        return [
            record
            for record in table_data
            if all(
                record.get(column) == value
                for column, value in where_clause.items()
            )
        ]

    return cache_result(cache_key, get_records)


def update(table_data, set_clause, where_clause):
    """Обновляет записи, соответствующие условию."""
    for record in table_data:
        if all(record.get(column) == value for column, value in where_clause.items()):
            record.update(set_clause)
    return table_data


@confirm_action("удаление записи")
def delete(table_data, where_clause):
    """Удаляет записи, соответствующие условию."""
    return [
        record
        for record in table_data
        if not all(
            record.get(column) == value for column, value in where_clause.items()
        )
    ]

