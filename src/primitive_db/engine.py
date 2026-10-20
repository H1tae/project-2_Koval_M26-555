import shlex

import prompt

from primitive_db.core import create_table, drop_table, list_tables
from primitive_db.utils import load_metadata, save_metadata

META_FILE = "db_meta.json"


def print_help():
    """Выводит справку по управлению таблицами."""
    print("\n***Процесс работы с таблицей***")
    print("Функции:")
    print(
        "<command> create_table <имя_таблицы> "
        "<столбец1:тип> <столбец2:тип> .. - создать таблицу"
    )
    print("<command> list_tables - показать список всех таблиц")
    print("<command> drop_table <имя_таблицы> - удалить таблицу")
    print("\nОбщие команды:")
    print("<command> exit - выход из программы")
    print("<command> help - справочная информация\n")


def run():
    """Запускает основной цикл управления таблицами."""
    print_help()

    while True:
        metadata = load_metadata(META_FILE)
        user_input = prompt.string(">>>Введите команду: ")

        try:
            args = shlex.split(user_input)
        except ValueError:
            print(f"Некорректное значение: {user_input}. Попробуйте снова.")
            continue

        if not args:
            print(f"Некорректное значение: {user_input}. Попробуйте снова.")
            continue

        command = args[0]

        if command == "exit":
            return
        if command == "help":
            print_help()
        elif command == "create_table":
            if len(args) < 3:
                print(f"Некорректное значение: {user_input}. Попробуйте снова.")
                continue

            table_name = args[1]
            table_existed = table_name in metadata
            updated_metadata = create_table(metadata, table_name, args[2:])
            if not table_existed and table_name in updated_metadata:
                save_metadata(META_FILE, updated_metadata)
        elif command == "drop_table":
            if len(args) != 2:
                print(f"Некорректное значение: {user_input}. Попробуйте снова.")
                continue

            table_name = args[1]
            table_existed = table_name in metadata
            updated_metadata = drop_table(metadata, table_name)
            if table_existed and table_name not in updated_metadata:
                save_metadata(META_FILE, updated_metadata)
        elif command == "list_tables":
            if len(args) != 1:
                print(f"Некорректное значение: {user_input}. Попробуйте снова.")
                continue
            list_tables(metadata)
        else:
            print(f"Функции {command} нет. Попробуйте снова.")

