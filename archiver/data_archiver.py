import logging
from jsonschema import validate, ValidationError
from kombu import Connection, Exchange, Producer
import config

class DataArchiver:

    INVALID_REQUEST = 'Invalid data archiving request'
    REQUEST_SUCCESSFUL = 'Data archiving request triggered successfully'
    REQUEST_FAILED = 'Data archiving request failed'

    def __init__(self, msg_broker):
        self.logger = logging.getLogger(__name__)
        self.msg_broker = msg_broker

    def send_request(self, req):
        try:
            validate(instance=req, schema=DataArchiver.data_archiver_request_format())
            self.logger.info(f'Received data archiving request: {req}')
            self.msg_broker.send(req)
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

class DataArchiverMessageBroker:
    RETRY_POLICY = {
        'interval_start': 0,
        'interval_step': 2,
        'interval_max': 30,
        'max_retries': 60
    }

    def __init__(self):
        self.conn = Connection(config.RABBITMQ_URL)
        self.channel = self.conn.channel()
        self.exchange = Exchange(config.RABBITMQ_DATA_ARCHIVER_EXCHANGE, type='topic')
        self.producer = Producer(exchange=self.exchange, channel=self.channel, routing_key=config.RABBITMQ_DATA_ARCHIVER_ROUTING_KEY)

    def send(self, msg):
        self.producer.publish(msg, retry=True, retry_policy=DataArchiverMessageBroker.RETRY_POLICY)
