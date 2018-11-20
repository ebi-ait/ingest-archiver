import json
import logging
import os
import sys

from optparse import OptionParser

from archiver.archiver import IngestArchiver


def save_output_to_file(output_dir, report):
    if not output_dir:
        return

    directory = os.path.abspath(output_dir)

    if not os.path.exists(directory):
        os.makedirs(directory)

    tmp_file = open(directory + "/" + bundle_uuid + ".json", "w")
    tmp_file.write(json.dumps(report, indent=4))
    tmp_file.close()

    print(f"Saved to {directory}/{bundle_uuid}.json!")


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

    (options, args) = parser.parse_args()

    if not (options.bundle_uuid or options.bundle_list_file):
        logging.error("You must supply a bundle UUID or a file with list of bundle uuids")
        exit(2)

    if not options.ingest_url:
        logging.error("You must supply the Ingest API url.")
        exit(2)

    exclude_types = []
    if options.exclude_types:
        exclude_types = [x.strip() for x in options.exclude_types.split(',')]
        logging.warning(f"Excluding {', '.join(exclude_types)}")

    bundles = [options.bundle_uuid]
    if options.bundle_list_file:
        with open(options.bundle_list_file) as f:
            content = f.readlines()

        bundle_list = [x.strip() for x in content]
        bundles = bundle_list

    archiver = IngestArchiver(ingest_url=options.ingest_url, exclude_types=exclude_types, alias_prefix=options.alias_prefix)

    if options.submission_url:
        print(f'##################### COMPLETING USI SUBMISSION {options.submission_url}')
        archive_submission = archiver.validate_and_complete_submission(options.submission_url)
        print('##################### SUMMARY')
        report = archive_submission.generate_report()
        save_output_to_file(options.output_dir, report)
    else:
        for bundle_uuid in bundles:
            print(f'##################### PROCESSING BUNDLE {bundle_uuid}')
            assay_bundle = archiver.get_assay_bundle(bundle_uuid)
            entities_dict = archiver.get_archivable_entities(assay_bundle)
            archive_submission = archiver.archive(entities_dict)
            print('##################### SUMMARY')
            report = archive_submission.generate_report()
            save_output_to_file(options.output_dir, report)
