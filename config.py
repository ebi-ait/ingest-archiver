import os

RABBITMQ_ARCHIVAL_QUEUE = 'ingest.archival.queue'
RABBITMQ_ARCHIVAL_QUEUE = os.environ.get('RABBITMQ_ARCHIVAL_QUEUE', RABBITMQ_ARCHIVAL_QUEUE)

RABBITMQ_SUBMITTED_QUEUE = 'ingest.envelope.submitted.queue'
RABBITMQ_SUBMITTED_QUEUE = os.environ.get('RABBITMQ_SUBMITTED_QUEUE', RABBITMQ_SUBMITTED_QUEUE)

RABBITMQ_SUBMITTED_EXCHANGE = 'ingest.envelope.submitted.exchange'
RABBITMQ_SUBMITTED_EXCHANGE = os.environ.get('RABBITMQ_SUBMITTED_EXCHANGE', RABBITMQ_SUBMITTED_EXCHANGE)

RABBITMQ_HOST = 'amqp://127.0.0.1'
RABBITMQ_PORT = '5672'
RABBITMQ_URL = RABBITMQ_HOST + ':' + RABBITMQ_PORT
RABBITMQ_URL = os.path.expandvars(os.environ.get('RABBITMQ_URL', RABBITMQ_URL))

INGEST_API_HOST = 'http://localhost'
INGEST_API_PORT = '8080'
INGEST_API_URL = INGEST_API_HOST + ':' + INGEST_API_PORT
INGEST_API_URL = os.path.expandvars(os.environ.get('INGEST_API', INGEST_API_URL))

AAP_API_URL = os.environ.get('AAP_API_URL', 'https://explore.api.aai.ebi.ac.uk/auth')
AAP_API_USER = 'hca-ingest'
AAP_API_PASSWORD = os.environ['AAP_API_PASSWORD'] if 'AAP_API_PASSWORD' in os.environ else ''
AAP_API_DOMAIN = 'subs.test-team-21'

USI_API_URL = 'https://submission-dev.ebi.ac.uk'

JSON_DIR = 'tests/json/'
ENCODING = 'utf-8'
