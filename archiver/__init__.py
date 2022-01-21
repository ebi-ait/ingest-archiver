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


class ArchiveResponse:

    def __init__(self, entity_type: str, accession: str = None, error_messages: List[str] = None):
        self.entity_type = entity_type
        self.accession = accession
        self.error_messages = error_messages
