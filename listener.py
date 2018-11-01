import pika
import os
import sys
import logging
import json

import polling

import config

from archiver.archiver import IngestArchiver, AssayBundle
from archiver.ingestapi import IngestAPI


class ArchiveBundleProcessor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.archiver = IngestArchiver()
        self.ingest_api = IngestAPI()

    def run(self, bundle_uuid):
        assay_bundle = AssayBundle(ingest_api=self.ingest_api,
                                   bundle_uuid=bundle_uuid)
        entities_dict_by_type = self.archiver.get_archivable_entities(assay_bundle)

        archive_submission = self.archiver.archive(entities_dict_by_type)

        self.logger.debug(archive_submission.to_str())

        if archive_submission.is_completed and archive_submission.processing_result:
            accessions = self.get_accessions(archive_submission)
            self.do_update_accessions_submission(accessions)
            self.logger.info("Done updating the accessions")

    def get_accessions(self, archive_submission):
        hca_samples_by_alias = archive_submission.entities_dict_type['samples']
        results = archive_submission.processing_result

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

    def do_update_accessions_submission(self, accessions):
        if not accessions:
            return

        new_submission = self.ingest_api.create_submission()
        self.logger.info("Creating new submission: " + str(new_submission))

        submission_samples_url = new_submission["_links"]["samples"]["href"].rsplit("{")[0]

        for accession in accessions:
            # the accessioning service must know some metadata schema to know how to update the schema
            content_patch = {
                "biomaterial_core": {
                    "biosd_biomaterial": accession['accession']
                }
            }
            sample_url = accession['entity_url']
            updated_sample = self.ingest_api.update_content(sample_url, content_patch)

            if updated_sample:
                self.ingest_api.link_samples_to_submission(submission_samples_url, sample_url)

        try:
            submit_url = polling.poll(
                lambda: self.ingest_api.get_submit_url(new_submission),
                step=5,
                timeout=60
            )
            self.ingest_api.submit(submit_url)
        except polling.TimeoutException:
            self.logger.error("Failed to do an update submission. The submission takes too long to get "
                              "validated and couldn't be submitted.")


class ArchiverListener:
    def __init__(self):
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        logging.basicConfig(level=logging.DEBUG, formatter=formatter)
        self.logger = logging.getLogger(__name__)

        self.rabbit = os.path.expandvars(config.RABBITMQ_URL)
        self.logger.debug("rabbit url is " + self.rabbit)

        self.queue = config.RABBITMQ_ARCHIVAL_QUEUE
        self.logger.debug("rabbit queue is " + self.queue)

        connection = pika.BlockingConnection(pika.URLParameters(self.rabbit))
        channel = connection.channel()
        self.channel = channel

        channel.queue_declare(queue=self.queue)

        def callback(ch, method, properties, body):

            self.logger.info(" [x] Received %r" % body)

            message = json.loads(str(body, config.ENCODING))
            hca_submission_uuid = message['documentUuid']

            if hca_submission_uuid:
                try:
                    processor = ArchiveBundleProcessor()
                    processor.run(hca_submission_uuid)
                except Exception as e:
                    self.logger.error(str(e))

        channel.basic_consume(callback,
                              queue=self.queue,
                              no_ack=True)
        self.logger.info(' [*] Waiting for messages from submission envelope')
        channel.start_consuming()


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    ArchiverListener()
