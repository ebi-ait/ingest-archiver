from archiver import ArchiveResponse


def create_archive_response(data, entity_type, is_update=False, error_messages=None):
    if error_messages is None:
        error_messages = []
    return ArchiveResponse(
        data=data,
        entity_type=entity_type,
        error_messages=error_messages,
        is_update=is_update
    )
