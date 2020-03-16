#!/usr/bin/env python3

# Sample usage:
#     python cli.py --project_uuid="2a0faf83-e342-4b1c-bb9b-cf1d1147f3bb"
#

import datetime
import json
import logging
import os
import sys
from optparse import OptionParser

import config
from archiver.archiver import IngestArchiver, ArchiveEntityMap
from api.ingest import IngestAPI
from api.ontology import OntologyAPI
from api.dsp import DataSubmissionPortal


class ArchiveCLI:
    def __init__(self, alias_prefix, output_dir, exclude_types, no_validation):
        self.manifests = []
        self.ingest_api = IngestAPI(config.INGEST_API_URL)

        now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H%M%S")
        self.output_dir = output_dir if output_dir else f"output/ARCHIVER_{now}"
        self.archiver = IngestArchiver(ingest_api=self.ingest_api,
                                       dsp_api=DataSubmissionPortal(config.DSP_API_URL),
                                       exclude_types=self.split_exclude_types(exclude_types),
                                       alias_prefix=alias_prefix,
                                       dsp_validation=not no_validation)

    def get_manifests_from_project(self, project_uuid):
        logging.info(f'GETTING MANIFESTS FOR PROJECT: {project_uuid}')
        self.manifests = self.ingest_api.get_manifest_ids(project_uuid=project_uuid)

    def get_manifests_from_list(self, manifest_list_file):
        logging.info(f'GETTING MANIFESTS FROM FILE: {manifest_list_file}')
        with open(manifest_list_file) as f:
            content = f.readlines()
        parsed_manifest_list = [x.strip() for x in content]
        self.manifests = parsed_manifest_list

    def complete_submission(self, submission_url):
        logging.info(f'##################### COMPLETING DSP SUBMISSION {submission_url}')
        archive_submission = self.archiver.complete_submission(submission_url)
        report = archive_submission.generate_report()
        submission_uuid = submission_url.rsplit('/', 1)[-1]
        self.save_dict_to_file(f'COMPLETE_SUBMISSION_{submission_uuid}', report)

    def build_map(self):
        logging.info(f'Processing {len(self.manifests)} manifests:\n' + "\n".join(map(str, self.manifests)))

        entity_map = self.archiver.convert(self.manifests)
        summary = entity_map.get_conversion_summary()
        logging.info(f'Entities to be converted: {json.dumps(summary)}')

        report = entity_map.generate_report()
        logging.info("Saving Report file...")
        self.save_dict_to_file("REPORT", report)
        return entity_map

    def validate_submission(self, entity_map: ArchiveEntityMap, submit):
        archive_submission = self.archiver.archive_metadata(entity_map)
        all_messages = self.archiver.notify_file_archiver(archive_submission)

        report = archive_submission.generate_report()
        logging.info("Updating Report file...")
        self.save_dict_to_file("REPORT", report)

        logging.info("##################### FILE ARCHIVER NOTIFICATION")
        self.save_dict_to_file("FILE_UPLOAD_INFO", {"jobs": all_messages})
        if submit:
            archive_submission.validate_and_submit()
        else:
            archive_submission.validate()

    def save_dict_to_file(self, file_name, json_content):
        if not self.output_dir:
            return

        directory = os.path.abspath(self.output_dir)

        if not os.path.exists(directory):
            os.makedirs(directory)

        file = directory + "/" + file_name + ".json"
        if os.path.exists(file):
            os.remove(file)

        with open(file, "w") as open_file:
            json.dump(json_content, open_file, indent=4)
            open_file.close()

        logging.info(f"Saved to {directory}/{file_name}.json!")

    @staticmethod
    def split_exclude_types(exclude_types):
        if exclude_types:
            exclude_types = [x.strip() for x in options.exclude_types.split(',')]
            logging.warning(f"Excluding {', '.join(exclude_types)}")
        return exclude_types


if __name__ == '__main__':
    logging_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(format=logging_format, stream=sys.stdout, level=logging.INFO)

    parser = OptionParser()

    # required
    parser.add_option("-p", "--project_uuid", help="Project UUID")

    # submit only
    parser.add_option("-u", "--submission_url",
                      help="DSP Submission url to complete")

    # options helpful for testing
    parser.add_option("-a", "--alias_prefix", help="Custom prefix to alias")
    parser.add_option("-x", "--exclude_types",
                      help="e.g. \"project,study,sample,sequencingExperiment,sequencingRun\"")
    parser.add_option("-f", "--manifest_list_file",
                      help="Specify a path to a file containing list of manifest id's to be archived."
                           "If project uuid is already specified then this parameter will be ignored.")

    # preferences
    parser.add_option("-s", "--submit",
                      help="Add this flag to wait for entities submit to archives once valid",
                      action="store_true", default=False)
    parser.add_option("-v", "--no_validation",
                      help="Add this flag to not send submission to DSP for validation, will override submit flag to false.",
                      action="store_true", default=False)
    parser.add_option("-o", "--output_dir", help="Customise output directory name")

    (options, args) = parser.parse_args()

    if not options.submission_url and not (options.project_uuid or options.manifest_list_file):
        logging.error("You must supply a project UUID or a file with list of manifest IDs")
        exit(2)

    cli = ArchiveCLI(options.alias_prefix, options.output_dir, options.exclude_types)
    if options.project_uuid:
        cli.get_manifests_from_project(options.project_uuid)
    elif options.manifest_list_file:
        cli.get_manifests_from_list(options.manifest_list_file)

    if options.submission_url:
        cli.complete_submission(options.submission_url)
    else:
        map = cli.build_map()
        if not options.no_validation:
            cli.validate_submission(map, options.submit)
