import pika
import os
import sys
import logging
import json
import config

from archiver.archiver import IngestArchiver
from archiver.ingestapi import IngestAPI


class ArchiveSubmissionProcessor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

        self.archiver = IngestArchiver()  # TODO dependency injection
        self.ingest_api = IngestAPI()

    def run(self, hca_submission_uuid):
        samples = self.ingest_api.get_samples_by_submission(hca_submission_uuid)
        hca_submission = {'samples': samples}

        summary = self.archiver.archive(hca_submission)  # TODO send message to archiver listener
        self.logger.info('---------------------')
        self.logger.info('summary:' + str(summary))
        self.logger.info('---------------------')

        # TODO these should happen in the accessioning service, move this
        if summary['is_completed']:
            accessions = self.get_accessions(summary)

            for accession in accessions:
                # the accessioning service must know some metadata schema to know how to update the schema
                content_patch = {
                    "sample_accessions": {
                        "biosd_sample": accession['accession']
                    }
                }
                self.ingest_api.update_content(accession['entity_url'], content_patch)

    def get_accessions(self, archive_summary):

        usi_submission = archive_summary['usi_submission']
        hca_samples_by_alias = archive_summary['hca_samples_by_alias']

        results = self.archiver.get_processing_results(usi_submission)

        accessions = []
        for result in results:
            if result['status'] == 'Completed':
                alias = result['alias']
                hca_sample = hca_samples_by_alias[alias]

                accession = {
                    'entity_url': hca_sample['_links']['self']['href'],
                    'accession': result['accession']
                }

                accessions.append(accession)

        return accessions


class ArchiverListener:
    def __init__(self):
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        logging.basicConfig(level=logging.DEBUG, formatter=formatter)
        self.logger = logging.getLogger(__name__)

        self.rabbit = os.path.expandvars(config.RABBITMQ_URL)
        self.logger.debug("rabbit url is " + self.rabbit)

        self.queue = config.RABBITMQ_ARCHIVAL_QUEUE
        self.logger.debug("rabbit queue is " + self.queue)

        connection = pika.BlockingConnection(pika.URLParameters(self.rabbit))  # TODO How to be async?
        channel = connection.channel()
        self.channel = channel

        channel.queue_declare(queue=self.queue)

        def callback(ch, method, properties, body):
            self.logger.info(" [x] Received %r" % body)

            message = json.loads(str(body, config.ENCODING))
            hca_submission_uuid = message['documentUuid']

            if hca_submission_uuid:
                try:
                    processor = ArchiveSubmissionProcessor()
                    processor.run(hca_submission_uuid)
                    self.notify_exporter(json.dumps(message))
                except Exception as e:
                    self.logger.error(str(e))

        channel.basic_consume(callback,
                              queue=self.queue,
                              no_ack=True)
        self.logger.info(' [*] Waiting for messages from submission envelope')
        channel.start_consuming()

    def notify_exporter(self, message):
        success = self.channel.basic_publish(exchange=config.RABBITMQ_SUBMITTED_EXCHANGE,
                                        routing_key=config.RABBITMQ_SUBMITTED_QUEUE,
                                        body=message)
        if not success:
            self.logger.error('Error in notifying the exporter')
        else:
            self.logger.info('notified exporter')
        return success


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    ArchiverListener()
