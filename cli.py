import datetime
import json
import logging
import os
import sys
import time

from optparse import OptionParser

from archiver.archiver import IngestArchiver
from archiver.usiapi import USIAPI
from archiver.ingestapi import IngestAPI


def save_dict_to_file(output_dir, filename, obj):
    if not output_dir:
        return

    directory = os.path.abspath(output_dir)

    if not os.path.exists(directory):
        os.makedirs(directory)

    with open(directory + "/" + filename + ".json", "w") as outfile:
        json.dump(obj, outfile, indent=4)

    print(f"Saved to {directory}/{filename}.json!")

if __name__ == '__main__':
    format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(format=format, stream=sys.stdout, level=logging.INFO)

    parser = OptionParser()
    parser.add_option("-b", "--bundle_uuid", help="Bundle UUID")
    parser.add_option("-i", "--ingest_url", help="Ingest API url")
    parser.add_option("-e", "--exclude_types", help="e.g. \"project,study,sample,sequencing_experiment,sequencing_run\"")
    parser.add_option("-f", "--bundle_list_file", help="Path to file containing list of bundle uuid's")
    parser.add_option("-o", "--output_dir", help="Output dir name")
    parser.add_option("-a", "--alias_prefix", help="Custom prefix to alias")
    parser.add_option("-s", "--submission_url", help="USI Submission url to complete")
    parser.add_option("-m", "--metadata_only", help="Archive the metadata only")
    parser.add_option("-p", "--project_uuid", help="Project UUID")

    (options, args) = parser.parse_args()

    if not (options.bundle_uuid or options.bundle_list_file):
        logging.error("You must supply a bundle UUID or a file with list of bundle uuids")
        exit(2)

    if not options.ingest_url:
        logging.error("You must supply the Ingest API url.")
        exit(2)

    ingest_api = IngestAPI(options.ingest_url)

    exclude_types = []
    if options.exclude_types:
        exclude_types = [x.strip() for x in options.exclude_types.split(',')]
        logging.warning(f"Excluding {', '.join(exclude_types)}")

    bundles = [options.bundle_uuid]
    if options.project_uuid:
        bundles = ingest_api.get_bundle_uuids(project_uuid=options.project_uuid)
    elif options.bundle_list_file:
        with open(options.bundle_list_file) as f:
            content = f.readlines()

        parsed_bundle_list = [x.strip() for x in content]
        bundles = parsed_bundle_list

    usi_api = USIAPI()
    archiver = IngestArchiver(ingest_api=ingest_api, usi_api=usi_api, exclude_types=exclude_types, alias_prefix=options.alias_prefix)

    if options.submission_url:
        print(f'##################### COMPLETING USI SUBMISSION {options.submission_url}')
        archive_submission = archiver.validate_and_complete_submission(options.submission_url)
        print('##################### SUMMARY')
        report = archive_submission.generate_report()
        submission_uuid = options.submission_url.rsplit('/', 1)[-1]
        save_dict_to_file(options.output_dir, f'COMPLETE_SUBMISSION_{submission_uuid}', report)
    else:
        all_messages = []
        for bundle_uuid in bundles:
            print(f'##################### PROCESSING BUNDLE {bundle_uuid}')
            assay_bundle = archiver.get_assay_bundle(bundle_uuid)
            entities_dict = archiver.convert(assay_bundle)
            if not options.metadata_only:
                archive_submission = archiver.archive(entities_dict)
            else:
                archive_submission = archiver.archive_metadata(entities_dict)
                messages = archiver.notify_file_archiver(archive_submission)
                all_messages.extend(messages)

            print('##################### SUMMARY')
            report = archive_submission.generate_report()
            save_dict_to_file(options.output_dir, f'ARCHIVE_{bundle_uuid}', report)

            # time.sleep(30)
        print(f'##################### FILE ARCHIVER NOTIFICATION')
        filename = f"file_archiver_notifications"
        save_dict_to_file(options.output_dir, filename, all_messages)
