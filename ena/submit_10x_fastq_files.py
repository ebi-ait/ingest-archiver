import argparse
import logging
import time

from api.ingest import IngestAPI
from ena.ena_api import EnaApi
from ena.util import write_xml

logging.getLogger('ena.ena_api').setLevel(logging.DEBUG)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Submits sequencing run entities to ENA')
    parser.add_argument('ingest_submission_uuid', type=str, help='Ingest submission UUID')
    parser.add_argument('md5_file', type=str, help='Filename containing md5 of files for the Ingest submission')
    parser.add_argument('--ftp_dir', type=str, required=False, help='Directory of files in the FTP upload area.')

    args = parser.parse_args()

    ingest_api = IngestAPI()
    ena_api = EnaApi(ingest_api)

    manifest_ids = ingest_api.get_manifest_ids_from_submission(args.ingest_submission_uuid)
    files = ena_api.create_xml_files(manifest_ids, args.md5_file, args.ftp_dir)

    result_xml_tree = ena_api.post_files(files)
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    write_xml(result_xml_tree, f'receipt_{timestamp}.xml')
