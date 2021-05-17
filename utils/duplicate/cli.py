import argparse
import os
import sys

from biosamples_v4.api import Client as BioSamplesClient
from ingest.api.ingestapi import IngestApi
from submission_broker.services.biosamples import BioSamples, AapClient

from converter.biosamples import BioSamplesConverter
from utils.duplicate.archiver import DuplicateArchiver


IGNORED_KEYS = [
    'accession',
    'domain',
    'relationships',
    'externalReferences',
    '_links',
    'create',
    'submitted',
    'submittedDate',
    'update',
    'updateDate',
    'release'
]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Re archive previously archived meta as new to testing environments.'
    )
    parser.add_argument(
        '--test_biosamples_domain', type=str,
        help='Set the BioSamples Domain for the Test BioSamples'
    )
    parser.add_argument(
        '--biosamples_accession', type=str,
        help='Regenerate and compate the biosample based on this accession'
    )
    parser.add_argument(
        '--project_uuid', type=str,
        help='Regenerate and compare all the biosamples in this project uuid'
    )
    parser.add_argument(
        '--test_biosamples_url', type=str, default='https://wwwdev.ebi.ac.uk/biosamples',
        help='Override the default URL for the Test BioSamples API: https://wwwdev.ebi.ac.uk/biosamples'
    )
    parser.add_argument(
        '--test_aap_url', type=str, default='https://explore.api.aai.ebi.ac.uk',
        help='Override the default URL for Test AAP API: https://explore.api.aai.ebi.ac.uk'
    )
    args = vars(parser.parse_args())
    if 'AAP_USERNAME' not in os.environ:
        print('No AAP_USERNAME detected in os environment variables.')
        sys.exit(2)
    if 'AAP_PASSWORD' not in os.environ:
        print('No AAP_PASSWORD detected in os environment variables.')
        sys.exit(2)

    prod_biosamples_url = 'https://www.ebi.ac.uk/biosamples'
    prod_ingest_url = 'https://api.ingest.archive.data.humancellatlas.org/'

    aap_client = AapClient(os.environ['AAP_USERNAME'], os.environ['AAP_PASSWORD'], args['test_aap_url'])
    archiver = DuplicateArchiver(IngestApi(prod_ingest_url), BioSamplesClient(prod_biosamples_url), BioSamples(aap_client, args['test_biosamples_url']), BioSamplesConverter(args['test_biosamples_domain']))
    if args['biosamples_accession']:
        archiver.compare_duplicate_biosample(args['biosamples_accession'], IGNORED_KEYS)
    elif args['project_uuid']:
        archiver.compare_duplicate_project(args['project_uuid'], IGNORED_KEYS)
