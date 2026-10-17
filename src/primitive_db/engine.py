import prompt


def welcome():
    """Запускает цикл обработки команд."""
    print("Первая попытка запустить проект!")
    print("\n***")
    print("<command> exit - выйти из программы")
    print("<command> help - справочная информация")

    while True:
        command = prompt.string("Введите команду: ")

        if command == "exit":
            return
        if command == "help":
            print("\n<command> exit - выйти из программы")
            print("<command> help - справочная информация")

