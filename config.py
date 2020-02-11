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
INGEST_API_URL = os.path.expandvars(os.environ.get('INGEST_API_URL', INGEST_API_URL))

AAP_API_URL = 'https://explore.api.aai.ebi.ac.uk/auth'
AAP_API_URL = os.environ.get('AAP_API_URL', AAP_API_URL)
AAP_API_USER = 'hca-ingest'
AAP_API_USER = os.environ.get('AAP_API_USER', AAP_API_USER)
AAP_API_PASSWORD = 'INSERT_PASSWORD'
AAP_API_PASSWORD = os.environ.get('AAP_API_PASSWORD', AAP_API_PASSWORD)

AAP_API_DOMAIN = 'subs.test-team-21'
AAP_API_DOMAIN = os.environ.get('AAP_API_DOMAIN', AAP_API_DOMAIN)


USI_API_URL = os.environ.get('USI_API_URL', 'https://submission-test.ebi.ac.uk')

JSON_DIR = os.path.dirname(__file__) + '/tests/json/'
ENCODING = 'utf-8'

# polling config
VALIDATION_POLLING_STEP = os.environ.get('VALIDATION_POLLING_STEP', 10)
VALIDATION_POLLING_TIMEOUT = os.environ.get('VALIDATION_POLLING_TIMEOUT', 60)
VALIDATION_POLL_FOREVER = os.environ.get('VALIDATION_POLL_FOREVER', True)

SUBMISSION_POLLING_STEP = os.environ.get('SUBMISSION_POLLING_STEP', 30)
SUBMISSION_POLLING_TIMEOUT = os.environ.get('SUBMISSION_POLLING_TIMEOUT', 120)
SUBMISSION_POLL_FOREVER = os.environ.get('SUBMISSION_POLL_FOREVER', True)

ONTOLOGY_API_URL = os.environ.get('ONTOLOGY_API_URL', 'https://ontology.staging.data.humancellatlas.org')