import logging
import polling as polling

from archiver.usiapi import USIAPI
from archiver.ingestapi import IngestAPI
from archiver.converter import Converter, ConversionError, SampleConverter

VALIDATION_POLLING_TIMEOUT = 10
VALIDATION_POLLING_STEP = 2

SUBMISSION_POLLING_STEP = 3
SUBMISSION_POLLING_TIMEOUT = 30


class IngestArchiver:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.usi_api = USIAPI()
        self.converter = SampleConverter()
        self.ingest_api = IngestAPI

    def archive(self, entities_dict_by_type):
        archive_submission = ArchiveSubmission()

        archive_submission.entities_dict_type = entities_dict_by_type

        converted_entities = self._get_converted_entities(entities_dict_by_type)

        if converted_entities:
            archive_submission.converted_entities = converted_entities
            archive_submission.usi_submission = self.usi_api.create_submission()
            self.add_entities_to_submission(archive_submission.usi_submission, archive_submission.converted_entities)
        else:
            archive_submission.is_completed = True
            return archive_submission

        is_validated = False
        try:
            is_validated = polling.poll(
                lambda: self.is_validated(archive_submission.usi_submission),
                step=VALIDATION_POLLING_STEP,
                timeout=VALIDATION_POLLING_TIMEOUT
            )
        except polling.TimeoutException as te:
            archive_submission.errors.append('USI validation takes too long to complete.')

        is_submittable = self.is_submittable(archive_submission.usi_submission)

        if not is_validated or not is_submittable:
            validation_summary = self.get_all_validation_result_details(archive_submission.usi_submission)
            archive_submission.errors.append('Failed in USI validation.')
            archive_submission.validation_result = validation_summary
            return archive_submission

        self.usi_api.update_submission_status(archive_submission.usi_submission, 'Submitted')

        try:
            archive_submission.is_completed = polling.poll(
                lambda: self.is_processing_complete(archive_submission.usi_submission),
                step=SUBMISSION_POLLING_STEP,
                timeout=SUBMISSION_POLLING_TIMEOUT
            )
            archive_submission.processing_result = self.get_processing_results(archive_submission.usi_submission)

        except polling.TimeoutException:
            archive_submission.errors.append("USI submission takes too long complete.")

        return archive_submission

    def _get_converted_entities(self, entities_dict_by_type):
        converted_entities = []
        for entity_type, entity_dict in entities_dict_by_type.items():
            for alias, entity in entity_dict.items():
                if entity.converted_data:
                    converted_entities.append(entity)
        return converted_entities

    def get_archivable_entities(self, bundle_uuid):
        archive_entities_by_type = {}
        archive_entities = self._get_samples(bundle_uuid)
        archive_entities_by_type['samples'] = archive_entities

        return archive_entities_by_type

    def _get_samples(self, bundle_uuid):
        archive_entities = {}
        sample_converter = SampleConverter()
        biomaterials = self.ingest_api.get_biomaterials_in_bundle(bundle_uuid)

        for biomaterial in biomaterials:
            archive_entity = ArchiveEntity()
            archive_entity.archive_entity_type = 'sample'
            archive_entity.id = self._generate_archive_entity_id(archive_entity.archive_entity_type, biomaterial)
            archive_entity.input_data = {'biomaterial': biomaterial}
            if IngestArchiver.is_metadata_accessioned(biomaterial):
                archive_entity.warnings.append('Already accessioned')
                archive_entities[archive_entity.id] = archive_entity
                continue
            try:
                archive_entity.converted_data = sample_converter.convert(archive_entity.input_data)
            except ConversionError as e:
                archive_entity.warnings.append(
                    f'An error occured converting the biomaterial ({json.loads(biomaterial)}) to a sample, {str(e)}')




            archive_entities[archive_entity.id] = archive_entity

        return archive_entities

    def _generate_archive_entity_id(self, archive_entity_type, hca_entity):
        uuid = hca_entity['uuid']['uuid'] # should always be present in an hca entity
        return f'{archive_entity_type}|{uuid}'

    def add_entities_to_submission(self, usi_submission, converted_entities):
        get_contents_url = usi_submission['_links']['contents']['href']
        contents = self.usi_api.get_contents(get_contents_url)

        for entity in converted_entities:
            create_entity_url = contents['_links'][f'{entity.archive_entity_type}s:create']['href']
            created_entity = self.usi_api.create_entity(create_entity_url, entity.converted_data)
            entity.usi_json = created_entity

    def convert_entities(self, entities_dict_by_type):
        converted_entities_dict = {}

        samples = entities_dict_by_type['samples']
        result = self._convert_to_samples(samples)
        converted_entities_dict['samples'] = result

        return converted_entities_dict

    def _get_converter(self, entity_type):
        return SampleConverter()

    def _create_entity(self):
        return {
            'content': {},
            'errors': [],
            'info': [],
            'warnings': []
        }

    def get_all_validation_result_details(self, usi_submission):
        get_validation_results_url = usi_submission['_links']['validationResults']['href']
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

    def is_submittable(self, usi_submission):
        get_status_url = usi_submission['_links']['submissionStatus']['href']
        submission_status = self.usi_api.get_submission_status(get_status_url)

        get_available_statuses_url = submission_status['_links']['availableStatuses']['href']
        available_statuses = self.usi_api.get_available_statuses(get_available_statuses_url)

        for status in available_statuses:
            if status['statusName'] == 'Submitted':
                return True

        return False

    def is_validated(self, usi_submission):
        get_validation_results_url = usi_submission['_links']['validationResults']['href']
        validation_results = self.usi_api.get_validation_results(get_validation_results_url)

        for validation_result in validation_results:
            if validation_result['validationStatus'] != "Complete":
                return False

        return True

    def is_validated_and_submittable(self, usi_submission):
        return self.is_validated(usi_submission) and self.is_submittable(usi_submission)

    def complete_submission(self, usi_submission):
        if self.is_validated_and_submittable(usi_submission):
            return self.usi_api.update_submission_status(usi_submission, 'Submitted')

        return None

    def is_processing_complete(self, usi_submission):
        results = self.usi_api.get_processing_results(usi_submission)
        for result in results:
            if result['status'] != "Completed":
                return False

        return True

    def delete_submission(self, usi_submission):
        delete_url = usi_submission['_links']['self:delete']['href']
        return self.usi_api.delete_submission(delete_url)

    def get_processing_results(self, usi_submission):
        return self.usi_api.get_processing_results(usi_submission)

    @staticmethod
    def is_metadata_accessioned(sample):
        return ("biomaterial_core" in sample["content"]) and ("biosd_biomaterial" in sample["content"]["biomaterial_core"])


class ArchiveSubmission:
    def __init__(self):
        self.usi_submission = {}
        self.hca_submission = {}
        self.hca_submission_by_alias = {}
        self.errors = []
        self.processing_result = []
        self.validation_result = []
        self.is_completed = False
        self.entities_dict_type = {}
        self.converted_entities = []

    def to_str(self):
        return str(vars(self))


class ArchiveEntity:
    def __init__(self):
        self.input_data = {}
        self.converted_data = {}
        self.errors = []
        self.warnings = []
        self.id = None
        self.archive_entity_type = None