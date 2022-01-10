def first_element_or_self(object_to_process):
    if isinstance(object_to_process, list):
        object_to_process = object_to_process[0]
    return object_to_process
