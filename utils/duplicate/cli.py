import argparse
import logging
import os
import sys

from biosamples_v4.api import Client as BioSamplesClient
from ingest.api.ingestapi import IngestApi
from submission_broker.services.biosamples import BioSamples, AapClient

from converter.biosamples import BioSamplesConverter
from .archiver import DuplicateArchiver


def duplicate(prod_ingest: IngestApi, prod_biosamples: BioSamplesClient, staging_biosamples: BioSamples, converter: BioSamplesConverter):
    archiver = DuplicateArchiver(prod_ingest, prod_biosamples, staging_biosamples, converter)
    submission, biomaterial_uuid = archiver.load_project_from_biosample('SAMEA7002623')
    archiver.send_biosample(submission, biomaterial_uuid)
    old_sample = submission.biosamples.get(biomaterial_uuid, {}).get('old', {})
    new_sample = submission.biosamples.get(biomaterial_uuid, {}).get('new', {})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Re archive previously archived meta as new to testing environments.'
    )
    parser.add_argument(
        '--test_biosamples_domain', type=str, default='subs.dev-team-311',
        help='Override the default URL for the Test BioSamples Domain.'
    )
    parser.add_argument(
        '--test_biosamples_url', type=str, default='https://wwwdev.ebi.ac.uk/biosamples',
        help='Override the default URL for the Test BioSamples API: https://wwwdev.ebi.ac.uk/biosamples'
    )
    parser.add_argument(
        '--test_aap_url', type=str, default='https://explore.api.aai.ebi.ac.ukuk',
        help='Override the default URL for Test AAP API: https://explore.api.aai.ebi.ac.uk'
    )
    parser.add_argument(
        '--log_level', '-l', type=str, default='INFO',
        help='Override the default logging level: INFO',
        choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG']
    )
    args = vars(parser.parse_args())
    numeric_level = getattr(logging, args['log_level'].upper(), None)
    if numeric_level:
        logging.basicConfig(level=numeric_level)
    if 'AAP_USERNAME' not in os.environ:
        logging.error('No AAP_USERNAME detected in os environment variables.')
        sys.exit(2)
    if 'AAP_PASSWORD' not in os.environ:
        logging.error('No AAP_PASSWORD detected in os environment variables.')
        sys.exit(2)

    prod_biosamples_url = 'https://www.ebi.ac.uk/biosamples'
    prod_ingest_url = 'https://api.ingest.archive.data.humancellatlas.org/'

    aap_client = AapClient(os.environ['AAP_USERNAME'], os.environ['AAP_PASSWORD'], args['test_aap_url'])
    duplicate(
        IngestApi(prod_ingest_url),
        BioSamplesClient(prod_biosamples_url),
        BioSamples(aap_client, args['test_biosamples_url']),
        BioSamplesConverter(args['test_biosamples_domain'])
    )
