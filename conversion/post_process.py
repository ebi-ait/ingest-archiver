
def prefix_with(*args):
    data = args[0]
    prefix = args[1]
    return f'{prefix}{data}'


# TODO make this an all-purpose date processor
def format_date(*args):
    date = args[0]
    return date.split('T')[0]


def concatenate_list(*args):
    items = args[0]
    return ' , '.join(items)


def default_to(*args):
    value = args[0]
    default_value = args[1]
    return default_value if value is None else value