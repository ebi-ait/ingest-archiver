class ArchiverException(Exception):
    pass


class IngestArchiveError:
    def __init__(self, error_code: str, message: str, details: dict):
        self.error_code = error_code
        self.message = message
        self.details = details
