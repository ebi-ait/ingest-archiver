import json
import logging

import polling as polling

import config

from archiver.converter import ConversionError, SampleConverter, ProjectConverter, \
    SequencingExperimentConverter, SequencingRunConverter, StudyConverter

from utils import protocols


def _print_same_line(string):
    print(f'\r{string}', end='')


class ArchiverError(Exception):
    """Base-class for all exceptions raised by this module."""


class ArchiveEntity:
    def __init__(self):
        self.data = {}
        self.conversion = {}
        self.errors = []
        self.warnings = []
        self.id = None
        self.archive_entity_type = None
        self.accession = None
        self.dsp_json = None
        self.dsp_current_version = None
        self.links = {}
        self.manifest_id = None

    def __str__(self):
        return str(vars(self))


class ArchiveEntityMap:
    def __init__(self):
        self.entities_dict_type = {}

    def add_entities(self, entities):
        for entity in entities:
            self.add_entity(entity)

    def add_entity(self, entity: ArchiveEntity):
        if not self.entities_dict_type.get(entity.archive_entity_type):
            self.entities_dict_type[entity.archive_entity_type] = {}
        self.entities_dict_type[entity.archive_entity_type][entity.id] = entity

    def get_entity(self, entity_type, archive_entity_id):
        if self.entities_dict_type.get(entity_type):
            return self.entities_dict_type[entity_type].get(archive_entity_id)
        return None

    def get_converted_entities(self):
        for entities_dict in self.entities_dict_type.values():
            for entity in entities_dict.values():
                if entity.conversion and not entity.errors:
                    yield entity

    def get_conversion_summary(self):
        summary = {}
        for entities_dict in self.entities_dict_type.values():
            for entity in entities_dict.values():
                if entity.conversion and not entity.errors:
                    if not summary.get(entity.archive_entity_type):
                        summary[entity.archive_entity_type] = 0
                    summary[entity.archive_entity_type] = summary[entity.archive_entity_type] + 1
        return summary

    def find_entity(self, alias):
        for entities_dict in self.entities_dict_type.values():
            if entities_dict.get(alias):
                return entities_dict.get(alias)
        return None

    def get_entities(self):
        entities = []
        for entity_type, entities_dict in self.entities_dict_type.items():
            if not entities_dict:
                continue
            for alias, entity in entities_dict.items():
                entities.append(entity)
        return entities

    def update(self, entity_type, entities: dict):
        if not self.entities_dict_type.get(entity_type):
            self.entities_dict_type[entity_type] = {}
        self.entities_dict_type[entity_type].update(entities)


class Manifest:
    def __init__(self, ingest_api, manifest_id):
        self.ingest_api = ingest_api

        self.manifest_id = manifest_id
        self.manifest = self.ingest_api.get_manifest_by_id(self.manifest_id)

        self.project = None
        self.biomaterials = None
        self.files = None
        self.assay_process = None
        self.library_preparation_protocol = None
        self.sequencing_protocol = None
        self.input_biomaterial = None

    def get_project(self):
        if not self.project:
            project_uuid = list(self.manifest['fileProjectMap'])[0]
            self.project = self.ingest_api.get_project_by_uuid(project_uuid)

        return self.project

    def get_biomaterials(self):
        if not self.biomaterials:
            self.biomaterials = self._init_biomaterials()

        return self.biomaterials

    def get_assay_process(self):
        if not self.assay_process:
            self.assay_process = self._init_assay_process()

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
            self.input_biomaterial = self._init_input_biomaterial()

        return self.input_biomaterial

    def _init_biomaterials(self):
        for biomaterial_uuid in list(self.manifest['fileBiomaterialMap']):
            yield self.ingest_api.get_biomaterial_by_uuid(biomaterial_uuid)

    def _init_assay_process(self):
        file_uuid = list(self.manifest['fileFilesMap'])[0]
        file = self.ingest_api.get_file_by_uuid(file_uuid)
        derived_by_processes = self.ingest_api.get_related_entity(file, 'derivedByProcesses', 'processes')
        if derived_by_processes:
            if len(derived_by_processes) > 1:
                raise ArchiverError(f'Manifest {self.manifest_id} has many assay processes.')
            return derived_by_processes[0]
        return None

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

    def _init_input_biomaterial(self):
        assay = self.get_assay_process()
        input_biomaterials = self.ingest_api.get_related_entity(assay, 'inputBiomaterials', 'biomaterials')

        if not input_biomaterials:
            raise ArchiverError('No input biomaterial found to the assay process.')

        # TODO get first for now, clarify if it's possible to have multiple and how to specify the links
        return input_biomaterials[0]


class ArchiveSubmission:
    def __init__(self, dsp_api, dsp_submission_url=None):
        self.submission = {}
        self.errors = list()
        self.processing_result = list()
        self.validation_result = list()
        self.is_completed = False
        self.converted_entities = list()
        self.entity_map = ArchiveEntityMap()
        self.dsp_api = dsp_api
        self.file_upload_info = list()
        self.accession_map = None
        self.invalid = False
        self.status = None

        if dsp_submission_url:
            self.submission = self.dsp_api.get_submission(dsp_submission_url)
            self.status = self.get_status()

    def get_status(self):
        get_status_url = self.submission['_links']['submissionStatus']['href']
        submission_status = self.dsp_api.get_submission_status(get_status_url)
        state = submission_status.get('status')
        return state

    def __str__(self):
        return str(vars(self))

    def add_entities(self, converted_entities):
        get_contents_url = self.submission['_links']['contents']['href']
        contents = self.dsp_api.get_contents(get_contents_url)

        entity: ArchiveEntity
        for entity in converted_entities:
            entity_link = self.dsp_api.get_entity_url(entity.archive_entity_type)
            create_entity_url = contents['_links'][f'{entity_link}:create']['href']

            created_entity = self.dsp_api.create_entity(create_entity_url, entity.conversion)
            entity.dsp_json = created_entity

    def validate(self):
        if not self.submission:
            return self

        is_validated = False
        try:
            is_validated = polling.poll(
                lambda: self.is_validated(),
                step=config.VALIDATION_POLLING_STEP,
                timeout=config.VALIDATION_POLLING_TIMEOUT if not config.VALIDATION_POLL_FOREVER else None,
                poll_forever=True if config.VALIDATION_POLL_FOREVER else False
            )
        except polling.TimeoutException as te:
            self.errors.append({
                "error_message": "DSP validation takes too long to complete.",
            })

        if is_validated and self.get_all_validation_errors():
            validation_summary = self.get_all_validation_result_details()
            self.errors.append({
                "error_message": "Failed in DSP validation.",
                "details": {
                    "dsp_validation_errors": self.get_all_validation_errors()
                }
            })
            self.validation_result = validation_summary
            return self

        return self

    def validate_and_submit(self):
        if not self.submission:
            return self

        print("Waiting for the submission to be validated in DSP...")

        is_validated = False
        try:
            is_validated = polling.poll(
                lambda: self.is_ready_to_submit(),
                step=config.VALIDATION_POLLING_STEP,
                timeout=config.VALIDATION_POLLING_TIMEOUT if not config.VALIDATION_POLL_FOREVER else None,
                poll_forever=True if config.VALIDATION_POLL_FOREVER else False
            )
        except polling.TimeoutException as te:
            self.errors.append({
                "error_message": "DSP validation takes too long to complete.",
            })

        if is_validated and self.get_all_validation_errors():
            validation_summary = self.get_all_validation_result_details()
            self.validation_result = validation_summary
            self.errors.append({
                "error_message": "Failed in DSP validation.",
                "details": {
                    "dsp_validation_errors": self.get_all_validation_errors()
                }
            })
            self.invalid = True

        if self.is_submittable():
            self.submit()

        return self

    def submit(self):
        self.dsp_api.update_submission_status(self.submission, 'Submitted')

        print("DSP Submission is submitted! Waiting for the submission result. Please do not submit again.")

        try:
            self.is_completed = polling.poll(
                lambda: self.is_processing_complete(),
                step=config.SUBMISSION_POLLING_STEP,
                timeout=config.SUBMISSION_POLLING_TIMEOUT if not config.SUBMISSION_POLL_FOREVER else None,
                poll_forever=True if config.SUBMISSION_POLL_FOREVER else False
            )

            self.process_result()

        except polling.TimeoutException:
            self.errors.append({
                "error_message": "DSP submission takes too long to complete.",
            })

    def process_result(self):
        self.processing_result = self.get_processing_results()
        accession_map = {}
        for result in self.processing_result:
            if result['status'] == 'Completed':
                alias = result['alias']
                accession = result['accession']
                accession_map[alias] = accession
            elif result['status'] == 'Error':
                self.errors.append(f"There was an error submitting a "
                                   f"{result.get('submittableType', '')} with alias {result.get('alias', '')} to "
                                   f"{result.get('archive', '')}.")
        self.accession_map = accession_map

        return self

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
        get_validation_results_url = self.submission['_links']['validationResults']['href']
        validation_results = self.dsp_api.get_validation_results(get_validation_results_url)

        summary = []
        for validation_result in validation_results:
            if validation_result['validationStatus'] == "Complete":
                details_url = validation_result['_links']['validationResult']['href']
                # TODO fix how what to put as projection param, check dsp documentation, removing any params for now
                details_url = details_url.split('{')[0]
                validation_result_details = self.dsp_api.get_validation_result_details(details_url)
                summary.append(validation_result_details)

        return summary

    def get_all_validation_errors(self):
        get_validation_results_url = self.submission['_links']['validationResults']['href']
        validation_results = self.dsp_api.get_validation_results(get_validation_results_url)

        errors = []
        for validation_result in validation_results:
            if validation_result['validationStatus'] == "Complete":
                details_url = validation_result['_links']['validationResult']['href']
                # TODO fix how what to put as projection param, check dsp documentation, removing any params for now
                details_url = details_url.split('{')[0]
                validation_result_details = self.dsp_api.get_validation_result_details(details_url)
                if validation_result_details.get('errorMessages'):
                    errors.append(validation_result_details.get('errorMessages'))

        return errors

    def is_submittable(self):
        get_status_url = self.submission['_links']['submissionStatus']['href']
        submission_status = self.dsp_api.get_submission_status(get_status_url)

        get_available_statuses_url = submission_status['_links']['availableStatuses']['href']
        available_statuses = self.dsp_api.get_available_statuses(get_available_statuses_url)

        for status in available_statuses:
            if status['statusName'] == 'Submitted':
                return True

        return False

    def is_validated(self):
        get_validation_results_url = self.submission['_links']['validationResults']['href']
        validation_results = self.dsp_api.get_validation_results(get_validation_results_url)

        for validation_result in validation_results:
            if validation_result['validationStatus'] != "Complete":
                return False

        return True

    def is_validated_and_submittable(self):
        return self.is_validated(self.submission) and self.is_submittable(self.submission)

    def is_processing_complete(self):
        results = self.dsp_api.get_processing_results(self.submission)
        for result in results:
            if result['status'] != "Completed" and result['status'] != "Error":
                return False

        return True

    def delete_submission(self):
        delete_url = self.submission['_links']['self:delete']['href']
        return self.dsp_api.delete_submission(delete_url)

    def get_processing_results(self):
        return self.dsp_api.get_processing_results(self.submission)

    def get_url(self):
        # TODO remove projection placeholder
        if self.submission:
            return self.submission['_links']['self']['href'].split('{')[0]

        return None

    def generate_report(self):
        report = {}
        report['completed'] = self.is_completed
        report['submission_errors'] = self.errors
        report['file_upload_info'] = self.file_upload_info

        if self.submission:
            report['submission_url'] = self.get_url()

        entities = {}
        entity: ArchiveEntity
        for entity in self.entity_map.get_entities():
            entities[entity.id] = {}
            entities[entity.id]['errors'] = entity.errors
            entities[entity.id]['accession'] = entity.accession
            entities[entity.id]['warnings'] = entity.warnings
            entities[entity.id]['converted_data'] = entity.conversion

            if entity.dsp_json:
                entities[entity.id]['entity_url'] = entity.dsp_json['_links']['self']['href']

        report['entities'] = entities
        report['accessions'] = self.accession_map

        if self.entity_map:
            report['conversion_summary'] = self.entity_map.get_conversion_summary()

        return report


class IngestArchiver:
    def __init__(self, ingest_api, dsp_api, ontology_api, exclude_types=None, alias_prefix=None):
        self.logger = logging.getLogger(__name__)
        self.ingest_api = ingest_api
        self.exclude_types = exclude_types if exclude_types else []
        self.alias_prefix = f"{alias_prefix}_" if alias_prefix else ""
        self.ontology_api = ontology_api
        self.dsp_api = dsp_api

        self.converter = {
            "project": ProjectConverter(ontology_api=ontology_api),
            "sample": SampleConverter(ontology_api=ontology_api),
            "study": StudyConverter(ontology_api=ontology_api),
            "sequencingRun": SequencingRunConverter(ontology_api=ontology_api),
            "sequencingExperiment": SequencingExperimentConverter(ontology_api=ontology_api)
        }

        self.converter['sample'].ingest_api = self.ingest_api

    def archive(self, entity_map: ArchiveEntityMap):
        archive_submission = self.archive_metadata(entity_map)
        self.notify_file_archiver(archive_submission)
        archive_submission.validate_and_submit()
        return archive_submission

    def archive_metadata(self, entity_map: ArchiveEntityMap):
        archive_submission = ArchiveSubmission(dsp_api=self.dsp_api)
        archive_submission.entity_map = entity_map

        converted_entities = list(entity_map.get_converted_entities())

        if converted_entities:
            archive_submission.converted_entities = converted_entities
            archive_submission.submission = self.dsp_api.create_submission()
            print(f"DSP SUBMISSION: {archive_submission.get_url()}")
            archive_submission.add_entities(archive_submission.converted_entities)
        else:
            archive_submission.is_completed = True
            archive_submission.errors.append({
                "error_message": "No entities found to submit."
            })
            return archive_submission

        return archive_submission

    def complete_submission(self, dsp_submission_url):
        archive_submission = ArchiveSubmission(dsp_api=self.dsp_api, dsp_submission_url=dsp_submission_url)

        if archive_submission.status == 'Draft':
            archive_submission.validate_and_submit()
        elif archive_submission.status == 'Completed':
            archive_submission.is_completed = True
            archive_submission.process_result()

        return archive_submission

    def get_manifest(self, manifest_id):
        return Manifest(ingest_api=self.ingest_api, manifest_id=manifest_id)

    def convert(self, manifests):
        entity_map = ArchiveEntityMap()
        for idx, manifest_id in enumerate(manifests):
            print(f'\n* PROCESSING MANIFEST {idx + 1}/{len(manifests)}: {manifest_id}')
            manifest = self.get_manifest(manifest_id)
            entities = self._convert(manifest)
            entity_map.add_entities(entities)
        return entity_map

    def _convert(self, manifest: Manifest):
        aggregator = ArchiveEntityAggregator(manifest, alias_prefix=self.alias_prefix)

        entities = []
        for archive_entity_type in ["project", "study", "sample", "sequencingExperiment", "sequencingRun"]:
            print(f"Finding {archive_entity_type} entities in manifest...")
            progress_ctr = 0

            if self.exclude_types and archive_entity_type in self.exclude_types:
                print(f"Skipping {archive_entity_type} entities in manifest...")
                continue

            for archive_entity in aggregator.get_archive_entities(archive_entity_type):
                progress_ctr = progress_ctr + 1
                _print_same_line(str(progress_ctr))

                converter = self.converter[archive_entity_type]

                current_version = self.dsp_api.get_current_version(archive_entity.archive_entity_type,
                                                                   archive_entity.id)
                if current_version and current_version.get('accession'):
                    archive_entity.accession = current_version.get('accession')
                    archive_entity.errors.append({
                        "error_message": f"This alias has already been submitted to DSP, accession: {archive_entity.accession}.",
                        "details": {
                            "current_version": current_version["_links"]["self"]["href"]
                        }
                    })
                elif current_version and not current_version.get('accession'):
                    archive_entity.errors.append({
                        "error_message": f'This alias has already been submitted to DSP, but still has no accession.',
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

                    except ConversionError as e:
                        archive_entity.errors.append({
                            "error_message": f'An error occured converting data to a {archive_entity_type}: {str(e)}.',
                            "details": {"data": json.loads(archive_entity.data)}
                        })

                entities.append(archive_entity)
            print("")

        return entities

    # TODO save notification to file for now, should be sending to rabbit mq in the future
    def notify_file_archiver(self, archive_submission: ArchiveSubmission):

        messages = []
        # TODO a bit redundant with converter, refactor this
        for entity in archive_submission.converted_entities:
            if entity.archive_entity_type == 'sequencingRun':
                data = entity.data
                files = []

                for file in data.get('files'):
                    obj = {
                        # required fields
                        "name": file['content']['file_core']['file_name'],
                        "read_index": file['content']['read_index'],
                        "cloud_url": file['cloudUrl']
                    }
                    files.append(obj)

                message = {
                    "dsp_api_url": self.dsp_api.url,
                    "ingest_api_url": self.ingest_api.url,
                    "submission_url": archive_submission.get_url(),
                    "files": files,
                    "manifest_id": entity.manifest_id
                }

                if protocols.is_10x(data.get("library_preparation_protocol")):
                    message["conversion"] = {}
                    message["conversion"]["output_name"] = f"{data['manifest_id']}.bam"
                    message["conversion"]["inputs"] = files
                    message["files"] = [f"{data['manifest_id']}.bam"]

                messages.append(message)

        archive_submission.file_upload_info = messages
        return messages

    @staticmethod
    def is_metadata_accessioned(entity: ArchiveEntity):
        if entity.archive_entity_type != "sample":
            return False

        sample = entity.data.get("biomaterial")
        if sample:
            return ("biomaterial_core" in sample["content"]) and ("biosd_biomaterial" in sample["content"]["biomaterial_core"])

        return False


class ArchiveEntityAggregator:
    def __init__(self, manifest: Manifest, alias_prefix):
        self.manifest = manifest
        self.alias_prefix = alias_prefix

    def _get_projects(self):
        project = self.manifest.get_project()
        if not project:
            return []
        archive_entity = ArchiveEntity()
        archive_type = "project"
        archive_entity.archive_entity_type = archive_type
        archive_entity.id = self.generate_archive_entity_id(archive_type, project)
        archive_entity.data = {"project": project}
        archive_entity.manifest_id = self.manifest.manifest_id
        return [archive_entity]

    def _get_studies(self):
        project = self.manifest.get_project()
        if not project:
            return []
        archive_entity = ArchiveEntity()
        archive_entity.manifest_id = self.manifest.manifest_id
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
        for biomaterial in self.manifest.get_biomaterials():
            archive_entity = ArchiveEntity()
            archive_entity.manifest_id = self.manifest.manifest_id
            archive_type = "sample"
            archive_entity.archive_entity_type = archive_type
            archive_entity.id = self.generate_archive_entity_id(archive_type, biomaterial)
            archive_entity.data = {"biomaterial": biomaterial}
            samples.append(archive_entity)
        return samples

    def _get_sequencing_experiments(self):
        process = self.manifest.get_assay_process()
        if not process:
            return []
        input_biomaterial = self.manifest.get_input_biomaterial()

        archive_entity = ArchiveEntity()
        archive_entity.manifest_id = self.manifest.manifest_id
        archive_type = "sequencingExperiment"
        archive_entity.archive_entity_type = archive_type
        archive_entity.id = self.generate_archive_entity_id(archive_type, process)
        archive_entity.data = {
            'process': process,
            'library_preparation_protocol': self.manifest.get_library_preparation_protocol(),
            'sequencing_protocol': self.manifest.get_sequencing_protocol(),
            'input_biomaterial': input_biomaterial
        }

        links = {}
        links['studyRef'] = {
            "alias": self.generate_archive_entity_id('study', self.manifest.get_project())
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
        process = self.manifest.get_assay_process()
        archive_entity = ArchiveEntity()
        archive_entity.manifest_id = self.manifest.manifest_id
        archive_type = "sequencingRun"
        archive_entity.archive_entity_type = archive_type
        archive_entity.id = self.generate_archive_entity_id(archive_type, process)
        archive_entity.data = {
            'library_preparation_protocol': self.manifest.get_library_preparation_protocol(),
            'process': self.manifest.get_assay_process(),
            'files': self.manifest.get_files(),
            'manifest_id': archive_entity.manifest_id
        }
        archive_entity.links = {
            'assayRefs': [{
                "alias": self.generate_archive_entity_id('sequencingExperiment', process)
            }]
        }
        return [archive_entity]

    def get_archive_entities(self, archive_entity_type):
        entities = []
        if archive_entity_type == "project":
            entities = self._get_projects()
        elif archive_entity_type == "study":
            entities = self._get_studies()
        elif archive_entity_type == "sample":
            entities = self._get_samples()
        elif archive_entity_type == "sequencingExperiment":
            entities = self._get_sequencing_experiments()
        elif archive_entity_type == "sequencingRun":
            entities = self._get_sequencing_runs()
        return entities

    def generate_archive_entity_id(self, archive_entity_type, entity):
        uuid = entity["uuid"]["uuid"]
        return f"{self.alias_prefix}{archive_entity_type}_{uuid}"
