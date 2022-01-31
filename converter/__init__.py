def fixed_attribute(*args):
    value = args[1]
    return value


def get_value_by_key_path(entity: dict, key_path: list) -> str:
    value = entity
    for key in key_path:
        value = value.get(key)
        if value is None:
            return value

    return value


def get_concrete_type(schema_url):
    concrete_type = schema_url.split('/')[-1]
    return concrete_type


def array_to_string(*args):
    value = ", ".join(args[0])
    return value
