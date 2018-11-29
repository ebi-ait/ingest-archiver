# Sample usage:
#     python cli.py --project_uuid="2a0faf83-e342-4b1c-bb9b-cf1d1147f3bb"
#

import datetime
import json
import logging
import os
import sys

import config

from optparse import OptionParser

from archiver.archiver import IngestArchiver, ArchiveEntityMap
from archiver.usiapi import USIAPI
from archiver.ingestapi import IngestAPI

ingest_url = config.INGEST_API_URL
usi_url = config.USI_API_URL

ingest_api = IngestAPI(ingest_url)
usi_api = USIAPI(usi_url)


def save_dict_to_file(output_dir, filename, obj):
    if not output_dir:
        return

    directory = os.path.abspath(output_dir)

    if not os.path.exists(directory):
        os.makedirs(directory)

    with open(directory + "/" + filename + ".json", "w") as outfile:
        json.dump(obj, outfile, indent=4)

    print(f"Saved to {directory}/{filename}.json!")


def get_exclude_types(options):
    exclude_types = []
    if options.exclude_types:
        exclude_types = [x.strip() for x in options.exclude_types.split(',')]
        logging.warning(f"Excluding {', '.join(exclude_types)}")

    return exclude_types


def get_bundles(options):
    bundles = []

    if options.project_uuid:
        bundles = ingest_api.get_bundle_uuids(project_uuid=options.project_uuid)
    elif options.bundle_list_file:
        with open(options.bundle_list_file) as f:
            content = f.readlines()
        parsed_bundle_list = [x.strip() for x in content]
        bundles = parsed_bundle_list

    return bundles


if __name__ == '__main__':
    format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(format=format, stream=sys.stdout, level=logging.INFO)

    parser = OptionParser()
    parser.add_option("-e", "--exclude_types", help="e.g. \"project,study,sample,sequencingExperiment,sequencingRun\"")
    parser.add_option("-f", "--bundle_list_file", help="Path to file containing list of bundle uuid's")
    parser.add_option("-o", "--output_dir", help="Output dir name")
    parser.add_option("-a", "--alias_prefix", help="Custom prefix to alias")
    parser.add_option("-s", "--submission_url", help="USI Submission url to complete")
    parser.add_option("-p", "--project_uuid", help="Project UUID")

    (options, args) = parser.parse_args()

    if not (options.project_uuid or options.bundle_list_file):
        logging.error("You must supply a project UUID or a file with list of bundle UUIDs")
        exit(2)

    now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H%M%S")
    output_dir = options.output_dir if options.output_dir else f"ARCHIVER_{now}"
    exclude_types = get_exclude_types(options)
    bundles = get_bundles(options)

    archiver = IngestArchiver(ingest_api=ingest_api,
                              usi_api=usi_api,
                              exclude_types=exclude_types,
                              alias_prefix=options.alias_prefix)

    if options.submission_url:
        print(f'##################### COMPLETING USI SUBMISSION {options.submission_url}')
        archive_submission = archiver.validate_and_complete_submission(options.submission_url)
        report = archive_submission.generate_report()
        submission_uuid = options.submission_url.rsplit('/', 1)[-1]
        save_dict_to_file(output_dir, f'COMPLETE_SUBMISSION_{submission_uuid}', report)

    if not options.submission_url:
        all_messages = []
        bundle_len = len(bundles)
        print(f'\nProcessing {bundle_len} bundles:')
        print(*bundles, sep="\n")

        entity_map = archiver.convert(bundles)
        summary = entity_map.get_conversion_summary()
        print(f'\nEntities to be converted: {json.dumps(summary, indent=4)}')
        archive_submission = archiver.archive_metadata(entity_map)
        all_messages = archiver.notify_file_archiver(archive_submission)
        archive_submission.validate()

        report = archive_submission.generate_report()
        print("Saving Report file...")
        save_dict_to_file(output_dir, f'REPORT', report)

        archive_submission.validate()

        print(f'##################### FILE ARCHIVER NOTIFICATION')
        filename = f"FILE_UPLOAD_INFO"
        save_dict_to_file(output_dir, filename, {"jobs": all_messages})
