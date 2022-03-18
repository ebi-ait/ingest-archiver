from typing import List


def first_element_or_self(object_to_process):
    if isinstance(object_to_process, list) and len(object_to_process) > 0:
        object_to_process = object_to_process[0]
    return object_to_process


class ArchiveException(Exception):
    """ Custom exception dealing with REST error responses. """

    def __init__(self, message: str, status_code: str, archive_name: str):
        super().__init__(message, status_code)
        self.message = message
        self.status_code = status_code
        self.archive_name = archive_name


class ConvertedEntity:
    def __init__(self, data, is_update: bool, hca_entity_type: str):
        self.data = data
        self.updated = is_update
        self.hca_entity_type = hca_entity_type


class ArchiveResponse:

    def __init__(self, entity_type: str, data: dict, is_update: bool, error_messages: List[str] = None):
        self.entity_type = entity_type
        self.data = data
        self.updated = is_update
        self.error_messages = error_messages
