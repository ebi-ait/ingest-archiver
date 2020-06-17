import json
from typing import List, Iterator

from typing import List

import polling

import config


class Error:
    def __init__(self, error_code: str, message: str, details: dict):
        self.error_code = error_code
        self.message = message
        self.details = details


class ArchiveEntity:
    def __init__(self):
        self.data = {}
        self.metadata_uuids = None
        self.accessioned_metadata_uuids = None
        self.conversion = {}
        self.errors: List['Error'] = []
        self.warnings = []
        self.id = None
        self.archive_entity_type = None
        self.accession = None
        self.dsp_json = None
        self.dsp_url = None
        self.dsp_uuid = None
        self.dsp_current_version = None
        self.links = {}
        self.manifest_id = None

    def __str__(self):
        return str(vars(self))

    @staticmethod
    def map_from_report(report_id, report_entity):
        entity = ArchiveEntity()
        entity.id = report_id
        entity.archive_entity_type = report_entity['type']
        entity.conversion = report_entity['converted_data']
        entity.accession = report_entity['accession']
        entity.errors = report_entity['errors']
        entity.warnings = report_entity['warnings']
        return entity

    @staticmethod
    def map_from_ingest_entity(ingest_entity: dict):
        entity = ArchiveEntity()
        entity.id = ingest_entity['alias']
        entity.archive_entity_type = ingest_entity.get('type')
        entity.conversion = ingest_entity['conversion']
        entity.accession = ingest_entity['accession']
        entity.errors = ingest_entity['errors']
        entity.metadata_uuids = ingest_entity['metadataUuids']
        entity.accessioned_metadata_uuids = ingest_entity['accessionedMetadataUuids']
        entity.dsp_url = ingest_entity['dspUrl']
        entity.dsp_uuid = ingest_entity['dspUuid']
        return entity

    def add_error(self, error_code, message, details=None):
        self.errors.append(Error(error_code, message, details))


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
        entities = []
        for entities_dict in self.entities_dict_type.values():
            for entity in entities_dict.values():
                if entity.conversion and not entity.errors:
                    entities.append(entity)
        return entities

    def get_conversion_summary(self):
        summary = {}
        for entities_dict in self.entities_dict_type.values():
            for entity in entities_dict.values():
                if entity.conversion and not entity.errors:
                    if not summary.get(entity.archive_entity_type):
                        summary[entity.archive_entity_type] = 0
                    summary[entity.archive_entity_type] = summary[entity.archive_entity_type] + 1
        return summary

    def generate_report(self):
        report = {}
        entities = {}
        entity: ArchiveEntity
        for entity in self.get_entities():
            entities[entity.id] = {}
            entities[entity.id]['type'] = entity.archive_entity_type
            entities[entity.id]['errors'] = [error.__dict__ for error in entity.errors]
            entities[entity.id]['accession'] = entity.accession
            entities[entity.id]['warnings'] = entity.warnings
            entities[entity.id]['converted_data'] = entity.conversion

            if entity.dsp_json:
                entities[entity.id]['entity_url'] = entity.dsp_json['_links']['self']['href']

        report['entities'] = entities
        report['conversion_summary'] = self.get_conversion_summary()

        return report

    def find_entity(self, alias):
        for entities_dict in self.entities_dict_type.values():
            if entities_dict.get(alias):
                return entities_dict.get(alias)
        return None

    def get_entities(self) -> List["ArchiveEntity"]:
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

    @staticmethod
    def map_from_report(report):
        entity_map = ArchiveEntityMap()
        for key, entity in report.items():
            entity_map.add_entity(ArchiveEntity.map_from_report(key, entity))
        return entity_map

    @staticmethod
    def map_from_ingest_entities(ingest_entities: Iterator['dict']):
        entity_map = ArchiveEntityMap()
        for ingest_entity in ingest_entities:
            entity = ArchiveEntity.map_from_ingest_entity(ingest_entity)
            entity_map.add_entity(entity)
        return entity_map


class ArchiveSubmission:
    def __init__(self, dsp_api, dsp_submission_url=None):
        self.submission = {}
        self.errors: List['Error'] = list()
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
        self.dsp_url = None
        self.dsp_submission_url = dsp_submission_url
        self.dsp_uuid = None

        if dsp_submission_url:
            self.submission = self.dsp_api.get_submission(dsp_submission_url)
            self.status = self.get_status()
            self.dsp_uuid = dsp_submission_url.rsplit('/', 1)[-1]

    def get_status(self):
        get_status_url = self.submission['_links']['submissionStatus']['href']
        submission_status = self.dsp_api.get_submission_status(get_status_url)
        state = submission_status.get('status')
        return state

    def __str__(self):
        return str(vars(self))

    def add_entity(self, entity: ArchiveEntity):
        get_contents_url = self.submission['_links']['contents']['href']
        contents = self.dsp_api.get_contents(get_contents_url)

        entity_link = self.dsp_api.get_entity_url(entity.archive_entity_type)
        create_entity_url = contents['_links'][f'{entity_link}:create']['href']

        created_entity = self.dsp_api.create_entity(create_entity_url, entity.conversion)
        entity.dsp_json = created_entity
        entity.dsp_url = created_entity['_links']['self']['href']
        entity.dsp_uuid = entity.dsp_url.rsplit('/', 1)[-1]

    def add_entities(self, converted_entities: List['ArchiveEntity']):
        for entity in converted_entities:
            self.add_entity(entity)

    def add_error(self, error_code, message, details=None):
        self.errors.append(Error(error_code, message, details))

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
            self.add_error('archive_submission.validate.timed_out',
                           'DSP validation takes too long to complete.')

        if is_validated and self.get_all_validation_errors():
            validation_summary = self.get_all_validation_result_details()
            self.add_error('archive_submission.validate.dsp_validation_errors',
                           'Failed in DSP validation.',
                           {
                               'dsp_validation_errors': self.get_all_validation_errors()
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
            self.add_error('archive_submission.validate_and_submit.timed_out',
                           'DSP validation takes too long to complete.')

        if is_validated and self.get_all_validation_errors():
            validation_summary = self.get_all_validation_result_details()
            self.validation_result = validation_summary
            self.add_error('archive_submission.validate_and_submit.dsp_validation_errors',
                           'Failed in DSP validation.',
                           {
                               'dsp_validation_errors': self.get_all_validation_errors()
                           })
            self.invalid = True

        if self.is_submittable():
            self.submit()

        return self

    def submit(self):
        self.dsp_api.update_submission_status(self.submission, 'Submitted')

        print("DSP Submission is submitted! Waiting for the submission result. Please do not complete again.")

        try:
            self.is_completed = polling.poll(
                lambda: self.is_processing_complete(),
                step=config.SUBMISSION_POLLING_STEP,
                timeout=config.SUBMISSION_POLLING_TIMEOUT if not config.SUBMISSION_POLL_FOREVER else None,
                poll_forever=True if config.SUBMISSION_POLL_FOREVER else False
            )

            self.process_result()

        except polling.TimeoutException:
            self.add_error('archive_submission.complete.timed_out',
                           'DSP submission takes too long to complete.')

    def process_result(self):
        self.processing_result = self.get_processing_results()
        accession_map = {}
        for result in self.processing_result:
            if result['status'] == 'Completed':
                alias = result['alias']
                accession = result['accession']
                accession_map[alias] = accession
                entity = self.entity_map.find_entity(alias)
                if entity:
                    entity.accession = accession
            elif result['status'] == 'Error':
                self.add_error('archive_submission.complete.error',
                               f"There was an error submitting a " +
                               f"{result.get('submittableType', '')} with alias {result.get('alias', '')} to " +
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

    def get_validation_error_report(self):
        get_validation_results_url = self.submission['_links']['validationResults']['href']
        validation_results = self.dsp_api.get_validation_results(get_validation_results_url)

        report = {}
        for validation_result in validation_results:
            if validation_result['validationStatus'] == "Complete":
                details_url = validation_result['_links']['validationResult']['href']
                details_url = details_url.split('{')[0]
                validation_result_details = self.dsp_api.get_validation_result_details(details_url)
                if validation_result_details.get('errorMessages'):
                    try:
                        submittable_href = validation_result_details['_links']['submittable']['href']
                    except KeyError:
                        submittable_href = False
                    report_key = submittable_href if submittable_href else 'NoSubmittable'
                    if not report.get(report_key):
                        report[report_key] = []
                        report[report_key].append(validation_result_details.get('errorMessages'))
        return report

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

    def get_blockers(self):
        return self.dsp_api.get_submission_blockers_summary(self.submission)

    def generate_report(self):
        report = {}
        map_report = self.entity_map.generate_report()
        report['entities'] = map_report['entities']
        report['conversion_summary'] = map_report['conversion_summary']

        if self.submission:
            report['submission_url'] = self.get_url()

        report['accessions'] = self.accession_map
        report['completed'] = self.is_completed
        report['submission_errors'] = [error.__dict__ for error in self.errors]
        report['file_upload_info'] = self.file_upload_info

        return report