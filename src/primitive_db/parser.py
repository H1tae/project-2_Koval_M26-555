import shlex


def _split_items(expression):
    """Разделяет выражение по запятым, сохраняя строки в кавычках."""
    lexer = shlex.shlex(expression, posix=False)
    lexer.whitespace = ","
    lexer.whitespace_split = True
    lexer.commenters = ""
    return [item.strip() for item in lexer if item.strip()]


def _parse_value(value):
    """Преобразует текстовое значение в поддерживаемый тип."""
    value = value.strip()

    if len(value) >= 2 and value[0] in {'"', "'"} and value[-1] == value[0]:
        return value[1:-1]
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False

    try:
        return int(value)
    except ValueError as error:
        raise ValueError(value) from error


def _parse_assignment(expression):
    """Преобразует выражение со знаком равенства в пару ключ-значение."""
    column, separator, value = expression.partition("=")
    column = column.strip()
    value = value.strip()
    if not separator or not column or not value:
        raise ValueError(expression)
    return column, _parse_value(value)


def parse_values(expression):
    """Разбирает список значений в круглых скобках."""
    expression = expression.strip()
    if not expression.startswith("(") or not expression.endswith(")"):
        raise ValueError(expression)

    values_text = expression[1:-1].strip()
    if not values_text:
        return []
    return [_parse_value(item) for item in _split_items(values_text)]


def parse_where_clause(expression):
    """Преобразует условие where в словарь."""
    column, value = _parse_assignment(expression)
    return {column: value}


def parse_set_clause(expression):
    """Преобразует выражения set в словарь."""
    assignments = (_parse_assignment(item) for item in _split_items(expression))
    return dict(assignments)

