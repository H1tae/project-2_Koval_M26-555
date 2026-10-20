VALID_TYPES = {"int", "str", "bool"}


def create_table(metadata, table_name, columns):
    """Создаёт таблицу и добавляет её структуру в метаданные."""
    if table_name in metadata:
        print(f'Ошибка: Таблица "{table_name}" уже существует.')
        return metadata

    for column in columns:
        column_parts = column.split(":")
        if (
            len(column_parts) != 2
            or not column_parts[0]
            or column_parts[1] not in VALID_TYPES
        ):
            print(f"Некорректное значение: {column}. Попробуйте снова.")
            return metadata

    table_columns = ["ID:int", *columns]
    metadata[table_name] = table_columns
    columns_text = ", ".join(table_columns)
    print(
        f'Таблица "{table_name}" успешно создана со столбцами: '
        f"{columns_text}"
    )
    return metadata


def drop_table(metadata, table_name):
    """Удаляет таблицу из метаданных."""
    if table_name not in metadata:
        print(f'Ошибка: Таблица "{table_name}" не существует.')
        return metadata

    del metadata[table_name]
    print(f'Таблица "{table_name}" успешно удалена.')
    return metadata


def list_tables(metadata):
    """Выводит названия существующих таблиц."""
    for table_name in metadata:
        print(f"- {table_name}")

