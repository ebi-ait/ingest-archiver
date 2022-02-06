import logging
from jsonschema import validate, ValidationError
from kombu import Producer

class DataArchiver:

    INVALID_REQUEST = 'Invalid data archiving request'
    REQUEST_SUCCESSFUL = 'Data archiving request triggered successfully'
    REQUEST_FAILED = 'Data archiving request failed'

    def __init__(self, producer):
        self.logger = logging.getLogger(__name__)
        self.producer = producer

    def handle_request(self, req):
        try:
            validate(instance=req, schema=DataArchiver.data_archiver_request_format())
            self.logger.info(f'Received data archiving request: {req}')
            self.producer.publish(req, retry=True)
            return {'message': DataArchiver.REQUEST_SUCCESSFUL}

        except ValidationError as e:
            self.logger.error(f'{DataArchiver.INVALID_REQUEST}: {str(e)}')
            return {'message': DataArchiver.INVALID_REQUEST}

        except Exception as e:
            self.logger.error(f'{DataArchiver.REQUEST_FAILED}: {str(e)}')
            return { 'message' : DataArchiver.REQUEST_FAILED}

    @staticmethod
    def data_archiver_request_format():
        return {
            "type": "object",
            "properties": {
                "sub_uuid": {"type": "string"},
                "files": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["sub_uuid"]
        }