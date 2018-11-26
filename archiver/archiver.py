import datetime
import json
import logging

import pika
import polling as polling

import config

from archiver.usiapi import USIAPI
from archiver.ingestapi import IngestAPI
from archiver.converter import ConversionError, SampleConverter, ProjectConverter, \
    SequencingExperimentConverter, SequencingRunConverter, StudyConverter

from archiver import util


def _print_same_line(string):
    print(f'\r{string}', end='')


class ArchiveEntity:
    def __init__(self):
        self.data = {}
        self.conversion = {}
        self.errors = []
        self.warnings = []
        self.id = None
        self.archive_entity_type = None
        self.accession = None
        self.usi_json = None
        self.usi_current_version = None
        self.links = {}

    def __str__(self):
        return str(vars(self))


class ArchiveEntityMap:
    def __init__(self):
        self.entities_dict_type = {}
        self.bundle_uuid = None
        self.bundle = None

    def add_entity(self, archive_entity_type, entity: ArchiveEntity):
        if not self.entities_dict_type.get(archive_entity_type):
            self.entities_dict_type[archive_entity_type] = {}
        self.entities_dict_type[archive_entity_type][entity.id] = entity

    def get_entity(self, entity_type, archive_entity_id):
        if self.entities_dict_type.get(entity_type):
            return self.entities_dict_type[entity_type].get(archive_entity_id)
        return None

    def update(self, entity_type, entities: dict):
        if not self.entities_dict_type.get(entity_type):
            self.entities_dict_type[entity_type] = {}
        self.entities_dict_type[entity_type].update(entities)

    def get_converted_entities(self):
        for entities_dict in self.entities_dict_type.values():
            for entity in entities_dict.values():
                if entity.conversion and not entity.errors:
                    yield entity


class ArchiveSubmission:
    def __init__(self, usi_api):
        self.usi_submission = {}
        self.errors = []
        self.processing_result = []
        self.validation_result = []
        self.is_completed = False
        self.entities_dict_type = {}
        self.converted_entities = []
        self.entity_map = None
        self.bundle_uuid = None

        self.usi_api = usi_api

    def __str__(self):
        return str(vars(self))

    def add_entities(self, converted_entities):
        get_contents_url = self.usi_submission['_links']['contents']['href']
        contents = self.usi_api.get_contents(get_contents_url)

        for entity in converted_entities:
            entity_link = self.usi_api.get_entity_url(entity.archive_entity_type)
            create_entity_url = contents['_links'][f'{entity_link}:create']['href']

            created_entity = self.usi_api.create_entity(create_entity_url, entity.conversion)
            entity.usi_json = created_entity

    def validate_and_submit(self):
        if not self.usi_submission:
            return self

        is_validated = False
        try:
            is_validated = polling.poll(
                lambda: self.is_ready_to_submit(),
                step=config.VALIDATION_POLLING_STEP,
                timeout=config.VALIDATION_POLLING_TIMEOUT if not config.VALIDATION_POLL_FOREVER else None,
                poll_forever=True if config.VALIDATION_POLL_FOREVER else False
            )
        except polling.TimeoutException as te:
            self.errors.append('USI validation takes too long to complete.')

        is_submittable = self.is_submittable()

        if not is_validated or not is_submittable:
            validation_summary = self.get_all_validation_result_details()
            self.errors.append('Failed in USI validation.')
            self.validation_result = validation_summary
            return self

        self.usi_api.update_submission_status(self.usi_submission, 'Submitted')

        try:
            self.is_completed = polling.poll(
                lambda: self.is_processing_complete(),
                step=config.SUBMISSION_POLLING_STEP,
                timeout=config.SUBMISSION_POLLING_TIMEOUT if not config.SUBMISSION_POLL_FOREVER else None,
                poll_forever=True if config.SUBMISSION_POLL_FOREVER else False
            )
            self.processing_result = self.get_processing_results()

            for result in self.processing_result:
                if result['status'] == 'Completed':
                    alias = result['alias']
                    accession = result['accession']
                    entity = self.find_entity(alias)
                    if entity:
                        entity.accession = accession

        except polling.TimeoutException:
            self.errors.append("USI submission takes too long complete.")

    def is_ready_to_submit(self):
        is_validated = self.is_validated()

        if is_validated:
            is_submittable = self.is_submittable()
            if is_submittable:
                return True
            else:
                errors = self.get_all_validation_errors()
                self.validation_result = errors
                print("####################### VALIDATION ERRORS")
                print(json.dumps(errors, indent=4))
                print("####################### SUBMISSION REPORT")
                print(json.dumps(self.generate_report(), indent=4))

        return False

    def get_all_validation_result_details(self):
        get_validation_results_url = self.usi_submission['_links']['validationResults']['href']
        validation_results = self.usi_api.get_validation_results(get_validation_results_url)

        summary = []
        for validation_result in validation_results:
            if validation_result['validationStatus'] == "Complete":
                details_url = validation_result['_links']['validationResult']['href']
                # TODO fix how what to put as projection param, check usi documentation, removing any params for now
                details_url = details_url.split('{')[0]
                validation_result_details = self.usi_api.get_validation_result_details(details_url)
                summary.append(validation_result_details)

        return summary

    def get_all_validation_errors(self):
        get_validation_results_url = self.usi_submission['_links']['validationResults']['href']
        validation_results = self.usi_api.get_validation_results(get_validation_results_url)

        errors = []
        for validation_result in validation_results:
            if validation_result['validationStatus'] == "Complete":
                details_url = validation_result['_links']['validationResult']['href']
                # TODO fix how what to put as projection param, check usi documentation, removing any params for now
                details_url = details_url.split('{')[0]
                validation_result_details = self.usi_api.get_validation_result_details(details_url)
                if validation_result_details.get('errorMessages'):
                    errors.append(validation_result_details.get('errorMessages'))

        return errors

    def is_submittable(self):
        get_status_url = self.usi_submission['_links']['submissionStatus']['href']
        submission_status = self.usi_api.get_submission_status(get_status_url)

        get_available_statuses_url = submission_status['_links']['availableStatuses']['href']
        available_statuses = self.usi_api.get_available_statuses(get_available_statuses_url)

        for status in available_statuses:
            if status['statusName'] == 'Submitted':
                return True

        return False

    def is_validated(self):
        get_validation_results_url = self.usi_submission['_links']['validationResults']['href']
        validation_results = self.usi_api.get_validation_results(get_validation_results_url)

        for validation_result in validation_results:
            if validation_result['validationStatus'] != "Complete":
                return False

        return True

    def is_validated_and_submittable(self):
        return self.is_validated(self.usi_submission) and self.is_submittable(self.usi_submission)

    def submit(self):
        if self.is_validated_and_submittable(self.usi_submission):
            return self.usi_api.update_submission_status(self.usi_submission, 'Submitted')

        return None

    def is_processing_complete(self):
        results = self.usi_api.get_processing_results(self.usi_submission)
        for result in results:
            if result['status'] != "Completed":
                return False

        return True

    def delete_submission(self):
        delete_url = self.usi_submission['_links']['self:delete']['href']
        return self.usi_api.delete_submission(delete_url)

    def get_processing_results(self):
        return self.usi_api.get_processing_results(self.usi_submission)

    def get_url(self):
        # TODO remove projection placeholder
        if self.usi_submission:
            return self.usi_submission['_links']['self']['href'].split('{')[0]

        return None

    def find_entity(self, alias):
        for entities_dict in self.entities_dict_type.values():
            if entities_dict.get(alias):
                return entities_dict.get(alias)
        return None

    def generate_report(self, output_to_file=None):
        report = {}
        report['completed'] = self.is_completed
        report['submission_errors'] = self.errors
        report['validation_result'] = self.validation_result
        report['entities'] = {}

        if self.usi_submission:
            report['submission_url'] = self.get_url()

        for type, entities_dict in self.entities_dict_type.items():
            if not entities_dict:
                continue
            for alias, entity in entities_dict.items():
                report[alias] = {}
                report[alias]['errors'] = entity.errors
                report[alias]['accession'] = entity.accession
                report[alias]['warnings'] = entity.warnings

                if entity.usi_json:
                    report[alias]['entity_url'] = entity.usi_json['_links']['self']['href']

        print(json.dumps(report, indent=4))

        if output_to_file:
            with open(output_to_file, 'w') as outfile:
                json.dump(report, outfile, indent=4)

        return report


class IngestArchiver:
    def __init__(self, ingest_api, usi_api, exclude_types=None, alias_prefix=None):
        self.logger = logging.getLogger(__name__)
        self.ingest_api = ingest_api
        self.exclude_types = exclude_types if exclude_types else []
        self.alias_prefix = f"{alias_prefix}_" if alias_prefix else ""

        self.usi_api = usi_api

        self.converter = {
            "project": ProjectConverter(),
            "sample": SampleConverter(),
            "study": StudyConverter(),
            "sequencing_run": SequencingRunConverter(),
            "sequencing_experiment": SequencingExperimentConverter()
        }

    def archive(self, entity_map: ArchiveEntityMap):
        archive_submission = self.archive_metadata(entity_map)
        # TODO Get all sequencing_run entities and notify file archiver
        self.notify_file_archiver(archive_submission)
        archive_submission.validate_and_submit()
        return archive_submission

    def archive_metadata(self, entity_map: ArchiveEntityMap):
        archive_submission = ArchiveSubmission(usi_api=self.usi_api)
        archive_submission.entity_map = entity_map
        archive_submission.entities_dict_type = entity_map.entities_dict_type

        converted_entities = list(entity_map.get_converted_entities())

        if converted_entities:
            archive_submission.converted_entities = converted_entities
            archive_submission.usi_submission = self.usi_api.create_submission()
            print("####################### USI SUBMISSION")
            print(archive_submission.usi_submission['_links']['self']['href'])
            archive_submission.add_entities(archive_submission.converted_entities)
        else:
            archive_submission.is_completed = True
            archive_submission.errors.append('No entities found to submit.')
            return archive_submission

        return archive_submission

    def validate_and_complete_submission(self, usi_submission_url):
        archive_submission = ArchiveSubmission(usi_api=self.usi_api)
        archive_submission.usi_submission = self.usi_api.get_submission(usi_submission_url)
        archive_submission.validate_and_submit()
        return archive_submission

    def get_assay_bundle(self, bundle_uuid):
        return AssayBundle(ingest_api=self.ingest_api, bundle_uuid=bundle_uuid)

    def convert(self, bundle):
        assay_bundles = [bundle]

        entity_map = None

        for assay_bundle in assay_bundles:
            entity_map = self._convert_entities(assay_bundle)
            entity_map.bundle_uuid = assay_bundle.bundle_uuid
            entity_map.bundle = assay_bundle

        return entity_map

    def _convert_entities(self, assay_bundle):
        aggregator = ArchiveEntityAggregator(assay_bundle, alias_prefix=self.alias_prefix)
        archive_entity_map = ArchiveEntityMap()
        summary = {}

        for archive_entity_type in ["project", "study", "sample", "sequencing_experiment", "sequencing_run"]:
            print(f"Finding {archive_entity_type} entities in the bundle...")
            progress_ctr = 0

            if self.exclude_types and archive_entity_type in self.exclude_types:
                print(f"Skipping {archive_entity_type} entities...")
                continue

            for archive_entity in aggregator.get_archive_entities(archive_entity_type):
                progress_ctr = progress_ctr + 1
                _print_same_line(str(progress_ctr))

                converter = self.converter[archive_entity_type]

                current_version = self.usi_api.get_current_version(archive_entity.archive_entity_type,
                                                                   archive_entity.id)

                if current_version and current_version.get('accession'):
                    archive_entity.accession = current_version.get('accession')
                    archive_entity.errors.append({
                        "error_message": f"This alias has already been submitted to USI, accession: {archive_entity.accession}.",
                        "details": {
                            "current_version": current_version["_links"]["self"]["href"]
                        }
                    })
                elif current_version and not current_version.get('accession'):
                    archive_entity.errors.append({
                        "error_message": f'This alias has already been submitted to USI, but still has no accession.',
                        "details": {
                            "current_version": current_version["_links"]["self"]["href"]
                        }
                    })

                elif IngestArchiver.is_metadata_accessioned(archive_entity):
                    archive_entity.errors.append({
                        "error_message": 'Metadata already have an accession'
                    })
                else:
                    try:
                        archive_entity.conversion = converter.convert(archive_entity.data)
                        archive_entity.conversion['alias'] = archive_entity.id
                        archive_entity.conversion.update(archive_entity.links)
                        if not summary.get(archive_entity_type):
                            summary[archive_entity_type] = 0

                        summary[archive_entity_type] = summary[archive_entity_type] + 1

                    except ConversionError as e:
                        archive_entity.errors.append({
                            "error_message": f'An error occured converting data to a {archive_entity_type}: {str(e)}.',
                            "details": {"data": json.loads(archive_entity.data)}
                        })

                archive_entity_map.add_entity(archive_entity_type, archive_entity)
            print("")
        print("Converted Entities Summary:")
        print(f"{json.dumps(summary, indent=4)}")

        return archive_entity_map

    # TODO specify rabbit connection details and construct message from entity
    def notify_file_archiver(self, archive_submission: ArchiveSubmission):
        # TODO send message to rabbit mq in the future
        # rabbit_url = ''
        # exchange = ''
        # routing_key = ''
        #
        # message = dict()
        #
        # connection = pika.BlockingConnection(pika.URLParameters(rabbit_url))
        # channel = connection.channel()
        # channel.basic_publish(exchange=exchange,
        #                       routing_key=routing_key,
        #                       body=json.dumps(message))
        # connection.close()

        message = {
            "usi_api_url": self.usi_api.url,
            "ingest_api_url": self.ingest_api.url,
            "submission_url": archive_submission.get_url(),
            "files": [],
            "bundle_uuid": archive_submission.entity_map.bundle_uuid
        }
        messages = []
        # TODO a bit redundant with converter, refactor this
        for entity in archive_submission.converted_entities:
            if entity.archive_entity_type == 'sequencingRun':
                data = entity.data
                files = []

                for file in data.get('files'):
                    files.append(file['content']['file_core']['file_name'])

                message["files"] = files

                if util.is_10x(data.get("library_preparation_protocol")):
                    message["conversion"] = {}
                    message["conversion"]["output_name"] = f"{data['bundle_uuid']}.bam"
                    files.sort()
                    message["conversion"]["inputs"] = files
                    message["files"] = [f"{data['bundle_uuid']}.bam"]

                messages.append(message)
                now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H%M%S")
                filename = f"file_archiver_notification_{archive_submission.entity_map.bundle_uuid}_{now}"
                with open(filename, 'w') as outfile:
                    json.dump(message, outfile, indent=4)
                    print(f"File Notification saved to {filename}")

        print(f"Notified file archiver: {json.dumps(messages, indent=4)}")



        return messages

    @staticmethod
    def is_metadata_accessioned(entity: ArchiveEntity):
        if entity.archive_entity_type != "sample":
            return False

        sample = entity.data.get("biomaterial")
        if sample:
            return ("biomaterial_core" in sample["content"]) and ("biosd_biomaterial" in sample["content"]["biomaterial_core"])

        return False


class AssayBundle:
    def __init__(self, ingest_api, bundle_uuid):
        self.ingest_api = ingest_api

        self.bundle_uuid = bundle_uuid
        self.bundle_manifest = None

        self.project = None
        self.biomaterials = None
        self.files = None
        self.assay_process = None
        self.library_preparation_protocol = None
        self.sequencing_protocol = None
        self.input_biomaterial = None

    def get_bundle_manifest(self):
        if not self.bundle_manifest:
            bundle_uuid = self.bundle_uuid
            self.bundle_manifest = self.ingest_api.get_bundle_manifest(bundle_uuid)

        return self.bundle_manifest

    def get_project(self):
        if not self.project:
            bundle_manifest = self.get_bundle_manifest()
            project_uuid = list(bundle_manifest['fileProjectMap'].keys())[0]  # TODO one project per bundle
            self.project = self.ingest_api.get_project_by_uuid(project_uuid)

        return self.project

    def get_biomaterials(self):
        if not self.biomaterials:
            self.biomaterials = self._init_biomaterials()

        return self.biomaterials

    def get_assay_process(self):
        bundle_manifest = self.get_bundle_manifest()
        file_uuid = list(bundle_manifest['fileFilesMap'].keys())[0]

        file = self.ingest_api.get_file_by_uuid(file_uuid)
        derived_by_processes = self.ingest_api.get_related_entity(file, 'derivedByProcesses', 'processes')

        if derived_by_processes:
            self.assay_process = derived_by_processes[0]

            if len(derived_by_processes) > 1:
                raise ArchiverError(f'Bundle {self.bundle_uuid} has many assay processes.')

        return self.assay_process

    def get_library_preparation_protocol(self):
        if not self.library_preparation_protocol:
            self._init_protocols()
        return self.library_preparation_protocol

    def get_sequencing_protocol(self):
        if not self.sequencing_protocol:
            self._init_protocols()
        return self.sequencing_protocol

    def get_files(self):
        if not self.files:
            assay = self.get_assay_process()
            self.files = self.ingest_api.get_related_entity(assay, 'derivedFiles', 'files')

        return self.files

    def get_input_biomaterial(self):
        if not self.input_biomaterial:
            self.input_biomaterial = self._retrieve_input_biomaterial()

        return self.input_biomaterial

    def _init_protocols(self):
        assay = self.get_assay_process()
        protocols = self.ingest_api.get_related_entity(assay, 'protocols', 'protocols')
        protocol_by_type = {}
        for protocol in protocols:
            concrete_entity_type = self.ingest_api.get_concrete_entity_type(protocol)
            if not protocol_by_type.get(concrete_entity_type):
                protocol_by_type[concrete_entity_type] = []

            protocol_by_type[concrete_entity_type].append(protocol)

        library_preparation_protocols = protocol_by_type.get('library_preparation_protocol', [])
        sequencing_protocols = protocol_by_type.get('sequencing_protocol', [])

        if len(library_preparation_protocols) != 1:
            raise ArchiverError('There should be 1 library preparation protocol for the assay process.')

        if len(sequencing_protocols) != 1:
            raise ArchiverError('There should be 1 sequencing_protocol for the assay process.')

        self.library_preparation_protocol = library_preparation_protocols[0]
        self.sequencing_protocol = sequencing_protocols[0]

    def _init_biomaterials(self):
        bundle_manifest = self.get_bundle_manifest()
        for biomaterial_uuid in bundle_manifest['fileBiomaterialMap'].keys():
            yield self.ingest_api.get_biomaterial_by_uuid(biomaterial_uuid)

    def _retrieve_input_biomaterial(self):
        assay = self.get_assay_process()
        input_biomaterials = self.ingest_api.get_related_entity(assay, 'inputBiomaterials', 'biomaterials')

        if not input_biomaterials:
            raise ArchiverError('No input biomaterial found to the assay process.')

        # TODO get first for now, clarify if it's possible to have multiple and how to specify the links
        return input_biomaterials[0]


class ArchiveEntityAggregator:
    def __init__(self, assay_bundle: AssayBundle, alias_prefix):
        self.assay_bundle = assay_bundle
        self.alias_prefix = alias_prefix

    def _get_projects(self):
        project = self.assay_bundle.get_project()
        if not project:
            return []
        archive_entity = ArchiveEntity()
        archive_type = "project"
        archive_entity.archive_entity_type = archive_type
        archive_entity.id = self.generate_archive_entity_id(archive_type, project)
        archive_entity.data = {"project": project}
        return [archive_entity]

    def _get_studies(self):
        project = self.assay_bundle.get_project()
        if not project:
            return []
        archive_entity = ArchiveEntity()
        archive_type = "study"
        archive_entity.archive_entity_type = archive_type
        archive_entity.id = self.generate_archive_entity_id(archive_type, project)
        archive_entity.data = {"project": project}
        archive_entity.links = {
            "projectRef": {
                "alias": self.generate_archive_entity_id('project', project)
            }
        }
        return [archive_entity]

    def _get_samples(self):
        samples = []
        for biomaterial in self.assay_bundle.get_biomaterials():
            archive_entity = ArchiveEntity()
            archive_type = "sample"
            archive_entity.archive_entity_type = archive_type
            archive_entity.id = self.generate_archive_entity_id(archive_type, biomaterial)
            archive_entity.data = {"biomaterial": biomaterial}
            samples.append(archive_entity)
        return samples

    def _get_sequencing_experiments(self):
        assay_bundle = self.assay_bundle
        process = assay_bundle.get_assay_process()
        if not process:
            return []
        input_biomaterial = assay_bundle.get_input_biomaterial()

        archive_entity = ArchiveEntity()
        archive_type = "sequencingExperiment"
        archive_entity.archive_entity_type = archive_type
        archive_entity.id = self.generate_archive_entity_id(archive_type, process)
        archive_entity.data = {
            'process': process,
            'library_preparation_protocol': assay_bundle.get_library_preparation_protocol(),
            'sequencing_protocol': assay_bundle.get_sequencing_protocol(),
            'input_biomaterial': input_biomaterial
        }

        links = {}
        links['studyRef'] = {
            "alias": self.generate_archive_entity_id('study', assay_bundle.get_project())
        }
        links['sampleUses'] = []
        sample_ref = {
            'sampleRef': {
                "alias": self.generate_archive_entity_id('sample', input_biomaterial)
            }
        }
        links['sampleUses'].append(sample_ref)

        archive_entity.links = links

        return [archive_entity]

    def _get_sequencing_runs(self):
        assay_bundle = self.assay_bundle
        process = assay_bundle.get_assay_process()
        archive_entity = ArchiveEntity()
        archive_type = "sequencingRun"
        archive_entity.archive_entity_type = archive_type
        archive_entity.id = self.generate_archive_entity_id(archive_type, process)
        archive_entity.data = {
            'library_preparation_protocol': assay_bundle.get_library_preparation_protocol(),
            'process': assay_bundle.get_assay_process(),
            'files': assay_bundle.get_files(),
            'bundle_uuid': assay_bundle.bundle_uuid
        }
        archive_entity.links = {
            'assayRefs': [{
                "alias": self.generate_archive_entity_id('sequencingExperiment', process)
            }]
        }
        return [archive_entity]

    def get_archive_entities(self, archive_entity_type):
        if archive_entity_type == "project":
            return self._get_projects()
        elif archive_entity_type == "study":
            return self._get_studies()
        elif archive_entity_type == "sample":
            return self._get_samples()
        elif archive_entity_type == "sequencing_experiment":
            return self._get_sequencing_experiments()
        elif archive_entity_type == "sequencing_run":
            return self._get_sequencing_runs()

    def generate_archive_entity_id(self, archive_entity_type, entity):
        uuid = entity["uuid"]["uuid"]
        return f"{self.alias_prefix}{archive_entity_type}_{uuid}"


class ArchiverError(Exception):
    """Base-class for all exceptions raised by this module."""
