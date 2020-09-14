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
from api.dsp import DataSubmissionPortal
from api.ingest import IngestAPI
from archiver.archiver import IngestArchiver, ArchiveEntityMap, ArchiveSubmission


class ArchiveCLI:
    def __init__(self, alias_prefix, output_dir, exclude_types, no_validation):
        self.manifests = []
        self.ingest_api = IngestAPI(config.INGEST_API_URL, config.INGEST_API_DOMAIN_NAME)
        self.dsp_api = DataSubmissionPortal(config.DSP_API_URL)
        now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H%M%S")
        self.output_dir = output_dir if output_dir else f"output/ARCHIVER_{now}"
        self.archiver = IngestArchiver(ingest_api=self.ingest_api,
                                       dsp_api=self.dsp_api,
                                       exclude_types=self.split_exclude_types(exclude_types),
                                       alias_prefix=alias_prefix,
                                       dsp_validation=not no_validation)

    def get_manifests_from_project(self, project_uuid):
        logging.info(f'GETTING MANIFESTS FOR PROJECT: {project_uuid}')
        self.manifests = self.ingest_api.get_manifest_ids_from_project(project_uuid=project_uuid)

    def get_manifests_from_submission(self, submission_uuid):
        logging.info(f'GETTING MANIFESTS FOR SUBMISSION: {submission_uuid}')
        self.manifests = self.ingest_api.get_manifest_ids_from_submission(submission_uuid)

    def get_manifests_from_list(self, manifest_list_file):
        logging.info(f'GETTING MANIFESTS FROM FILE: {manifest_list_file}')
        with open(manifest_list_file) as f:
            content = f.readlines()
        parsed_manifest_list = [x.strip() for x in content]
        self.manifests = parsed_manifest_list

    def complete_submission(self, dsp_submission_url):
        logging.info(f'##################### COMPLETING DSP SUBMISSION {dsp_submission_url}')
        archive_submission = ArchiveSubmission(dsp_api=self.archiver.dsp_api, dsp_submission_url=dsp_submission_url)
        ingest_archive_submission = self.ingest_api.get_archive_submission_by_dsp_uuid(archive_submission.dsp_uuid)
        ingest_entities = self.ingest_api.get_related_entity(ingest_archive_submission, 'entities', 'archiveEntities')
        entity_map = ArchiveEntityMap.map_from_ingest_entities(ingest_entities)
        archive_submission = self.archiver.complete_submission(dsp_submission_url, entity_map)
        report = archive_submission.generate_report()
        self.save_dict_to_file(f'COMPLETE_SUBMISSION_{archive_submission.dsp_uuid}', report)

    def build_map(self):
        logging.info(f'Processing {len(self.manifests)} manifests:\n' + "\n".join(map(str, self.manifests)))

        entity_map: ArchiveEntityMap = self.archiver.convert(self.manifests)
        summary = entity_map.get_conversion_summary()
        logging.info(f'Entities to be converted: {json.dumps(summary)}')

        report = entity_map.generate_report()
        logging.info("Saving Report file...")
        self.save_dict_to_file("REPORT", report)
        return entity_map

    def load_map(self, load_path):
        logging.info(f'Loading Entity Map: {load_path}')
        file_content: dict = self.load_dict_from_file(load_path)
        if file_content.get('entities'):
            return ArchiveEntityMap.map_from_report(file_content['entities'])
        logging.error(f"--load_path files does not have an entities object: {file_content}")
        exit(2)

    def validate_submission(self, entity_map: ArchiveEntityMap, submit, ingest_submission_uuid=None):
        archive_submission, ingest_archive_submission = self.archiver.archive_metadata(entity_map)
        all_messages = self.archiver.notify_file_archiver(archive_submission)
        ingest_archive_submission.patch_archive_submission({
            'submissionUuid': ingest_submission_uuid,
            'fileUploadPlan': archive_submission.file_upload_info
        })
        report = archive_submission.generate_report()
        logging.info("Updating Report file...")
        self.save_dict_to_file("REPORT", report)

        logging.info("##################### FILE ARCHIVER NOTIFICATION")
        self.save_dict_to_file("FILE_UPLOAD_INFO", {"jobs": all_messages})
        if submit:
            archive_submission.validate_and_submit()
        else:
            archive_submission.validate()

    def generate_validation_error_report(self, dsp_submission_url):
        submission = ArchiveSubmission(dsp_api=self.archiver.dsp_api, dsp_submission_url=dsp_submission_url)
        self.save_dict_to_file("VALIDATION_ERROR_REPORT", submission.get_validation_error_report())

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
    def load_dict_from_file(file_path):
        path = os.path.abspath(file_path)
        if os.path.exists(path) and os.path.isfile(path):
            with open(path, 'r') as open_file:
                content = open_file.read()
            return json.loads(content)
        else:
            logging.error(f"--load_path does not exist or is not a file: {file_path}")
            exit(2)

    @staticmethod
    def split_exclude_types(exclude_types):
        if exclude_types:
            exclude_types = [x.strip() for x in exclude_types.split(',')]
            logging.warning(f"Excluding {', '.join(exclude_types)}")
        return exclude_types


def exit_error(message: str):
    logging.error(message)
    exit(2)


def exit_success(message: str = None):
    if message:
        logging.info(message)
    exit(0)


if __name__ == '__main__':
    logging_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(format=logging_format, stream=sys.stdout, level=logging.INFO)

    parser = OptionParser()

    # required (1 of possible 3)
    parser.add_option("-p", "--project_uuid", help="Project UUID")

    parser.add_option("-i", "--ingest_submission_uuid", help="Ingest Submission UUID")

    parser.add_option("-f", "--manifest_list_file",
                      help="Specify a path to a file containing list of manifest id's to be archived."
                           "If project uuid is already specified then this parameter will be ignored.")

    parser.add_option("-l", "--load_path",
                      help="Specify the path to load a REPORT.json to send  to DSP, will skip loading and converting "
                           "from ingest.")

    # complete only
    parser.add_option("-u", "--submission_url",
                      help="DSP Submission url to complete")

    # validate only
    parser.add_option("-e", "--validation_errors",
                      action="store_true",
                      help="Generate validation errors report.")

    # options helpful for testing
    parser.add_option("-a", "--alias_prefix", help="Custom prefix to alias")
    parser.add_option("-x", "--exclude_types",
                      help="e.g. \"project,study,sample,sequencingExperiment,sequencingRun\"")

    # preferences
    parser.add_option("-s", "--submit",
                      help="Add this flag to wait for entities complete to archives once valid",
                      action="store_true", default=False)
    parser.add_option("-n", "--no_validation",
                      help="Add this flag to not send submission to DSP for validation, will override complete flag to "
                           "false.",
                      action="store_true", default=False)
    parser.add_option("-o", "--output_dir", help="Customise output directory name")

    (options, args) = parser.parse_args()

    if not (options.project_uuid or options.ingest_submission_uuid or options.manifest_list_file or options.load_path or options.submission_url):
        exit_error("You must supply one of the following "
                   "(1) a project UUID "
                   "(2) ingest submission uuid "
                   "(3) a file with list of manifest IDs "
                   "(4) a file of entities (4) a DSP submission url")

    if options.validation_errors and options.no_validation:
        exit_error("--validation_errors and --no_validation are mutually exclusive")

    if options.validation_errors and not options.submission_url:
        exit_error("--validation_errors requires --submission_url")

    if options.submission_url and options.load_path:
        logging.warning("When loading entities from disk, accessions won't be saved to ingest")

    cli = ArchiveCLI(options.alias_prefix, options.output_dir, options.exclude_types, options.no_validation or options.submission_url)

    if options.validation_errors and options.submission_url:
        cli.generate_validation_error_report(options.submission_url)
        exit_success()

    entity_map: ArchiveEntityMap
    if options.load_path:
        entity_map = cli.load_map(options.load_path)
    else:
        if options.project_uuid:
            cli.get_manifests_from_project(options.project_uuid)
        elif options.ingest_submission_uuid:
            cli.get_manifests_from_submission(options.ingest_submission_uuid)
        elif options.manifest_list_file:
            cli.get_manifests_from_list(options.manifest_list_file)
        entity_map = cli.build_map()

    if options.submission_url:
        cli.complete_submission(options.submission_url)
    elif entity_map and not options.no_validation:
        cli.validate_submission(entity_map, options.submit, ingest_submission_uuid=options.ingest_submission_uuid)

    exit_success()
