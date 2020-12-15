import json
import logging
from typing import Tuple

from api import ontology
from api.dsp import DataSubmissionPortal
from api.ingest import IngestAPI
from archiver.accessioner import Accessioner
from archiver.entity_aggregator import ArchiveEntityAggregator
from archiver.ingest_tracker import IngestTracker
from archiver.manifest import Manifest
from archiver.entity_map import ArchiveEntityMap
from utils import protocols
from .converter.biosample import BiosampleConverter
from .converter.biostudy import BiostudyConverter
from .converter.ena_experiment import EnaExperimentConverter
from .converter.ena_run import EnaRunConverter
from .converter.ena_study import EnaStudyConverter
from .converter.errors import DspConversionException
from .submission import DspSubmission


class DspBroker:
    def __init__(self, ingest_api: IngestAPI, dsp_api: DataSubmissionPortal,
                 ontology_api=ontology.__api__, exclude_types=None, alias_prefix=None,
                 dsp_validation=True):

        self.logger = logging.getLogger(__name__)
        self.ingest_api = ingest_api
        self.exclude_types = exclude_types if exclude_types else []
        self.alias_prefix = f"{alias_prefix}_" if alias_prefix else ""
        self.ontology_api = ontology_api
        self.dsp_api = dsp_api
        self.dsp_validation = dsp_validation
        self.accessioner = Accessioner(self.ingest_api)
        self.ingest_tracker = IngestTracker(ingest_api=self.ingest_api)

        self.converters = {
            "project": BiostudyConverter(),
            "sample": BiosampleConverter(ontology_api=ontology_api),
            "study": EnaStudyConverter(),
            "sequencingRun": EnaRunConverter(ontology_api=ontology_api),
            "sequencingExperiment": EnaExperimentConverter(ontology_api=ontology_api)
        }

    def archive(self, entity_map: ArchiveEntityMap):
        archive_submission, tracker = self.archive_metadata(entity_map)
        self.notify_file_archiver(archive_submission)
        archive_submission.validate_and_submit()
        return archive_submission

    def archive_metadata(self, entity_map: ArchiveEntityMap) -> Tuple[DspSubmission, IngestTracker]:
        archive_submission = DspSubmission(dsp_api=self.dsp_api)
        archive_submission.entity_map = entity_map

        converted_entities = entity_map.get_converted_entities()

        if converted_entities:
            archive_submission.converted_entities = converted_entities
            archive_submission.submission = self.dsp_api.create_submission()
            dsp_submission_url = archive_submission.get_url()
            archive_submission.dsp_url = dsp_submission_url
            archive_submission.dsp_uuid = dsp_submission_url.rsplit('/', 1)[-1]
            output = f"DSP SUBMISSION: {dsp_submission_url}"
            print(output)
            self.logger.info(output)
            ingest_tracker = self.ingest_tracker
            ingest_tracker.create_archive_submission(archive_submission)

            for entity in converted_entities:
                archive_submission.add_entity(entity)
                ingest_tracker.add_entity(entity)

        else:
            archive_submission.is_completed = True
            archive_submission.add_error('ingest_archiver.archive_metadata.no_entities',
                                         'No entities found to convert.')
            ingest_tracker = IngestTracker(ingest_api=self.ingest_api)
            ingest_tracker.create_archive_submission(archive_submission)
            return archive_submission, ingest_tracker

        return archive_submission, ingest_tracker

    def complete_submission(self, dsp_submission_url, entity_map: ArchiveEntityMap = None):
        archive_submission = DspSubmission(dsp_api=self.dsp_api, dsp_submission_url=dsp_submission_url)

        if entity_map:
            archive_submission.entity_map = entity_map
            archive_submission.converted_entities = list(archive_submission.entity_map.get_converted_entities())

        if archive_submission.status == 'Draft':
            archive_submission.validate_and_submit()
        elif archive_submission.status == 'Completed':
            archive_submission.is_completed = True

        archive_submission.process_result()
        self.ingest_tracker.update_entities(archive_submission.dsp_uuid, entity_map)
        self.accessioner.accession_entities(archive_submission.entity_map)
        self.ingest_tracker.set_submission_as_archived(archive_submission)

        return archive_submission

    def get_manifest(self, manifest_id):
        return Manifest(ingest_api=self.ingest_api, manifest_id=manifest_id)

    def convert(self, manifests) -> ArchiveEntityMap:
        entity_map = ArchiveEntityMap()
        idx = 0
        for manifest_url in manifests:
            idx = idx + 1
            manifest_id = manifest_url.rsplit('/', 1)[-1]
            print(f'\n* PROCESSING MANIFEST {idx}/{len(manifests)}: {manifest_id}')
            manifest = self.get_manifest(manifest_id)
            entities = self._convert(manifest)
            entity_map.add_entities(entities)
        return entity_map

    def _convert(self, manifest: Manifest):
        aggregator = ArchiveEntityAggregator(manifest, self.ingest_api, alias_prefix=self.alias_prefix)

        entities = []
        for archive_entity_type in ["project", "study", "sample", "sequencingExperiment", "sequencingRun"]:
            print(f"Finding {archive_entity_type} entities in manifest...")
            progress_ctr = 0

            if self.exclude_types and archive_entity_type in self.exclude_types:
                print(f"Skipping {archive_entity_type} entities in manifest...")
                continue

            for archive_entity in aggregator.get_archive_entities(archive_entity_type):
                progress_ctr = progress_ctr + 1
                print(f'\r{str(progress_ctr)}', end='')

                converter = self.converters[archive_entity_type]

                if self.dsp_validation:
                    current_version = self.dsp_api.get_current_version(archive_entity.archive_entity_type,
                                                                       archive_entity.id)
                    if current_version and current_version.get('accession'):
                        archive_entity.accession = current_version.get('accession')
                        msg = f'This alias has already been submitted to DSP, accession: {archive_entity.accession}.'
                        archive_entity.add_error('ingest_archiver.convert.entity_already_in_dsp_and_has_accession', msg,
                                                 {
                                                     "current_version": current_version["_links"]["self"]["href"]
                                                 })
                    elif current_version and not current_version.get('accession'):
                        msg = f'This alias has already been submitted to DSP, but still has no accession.'
                        archive_entity.add_error('ingest_archiver.convert.entity_already_in_dsp', msg, {
                            "current_version": current_version["_links"]["self"]["href"]
                        })
                    elif Accessioner.is_metadata_accessioned(archive_entity):
                        msg = f'Metadata already have an accession'
                        archive_entity.add_error('ingest_archiver.convert.entity_has_accession', msg, {
                            "current_version": current_version["_links"]["self"]["href"]
                        })

                if not archive_entity.errors:
                    try:
                        archive_entity.conversion = converter.convert(archive_entity.data)
                        archive_entity.conversion['alias'] = archive_entity.id
                        archive_entity.conversion.update(archive_entity.links)

                    except DspConversionException as e:
                        msg = f'An error occurred converting data to a {archive_entity_type}: {str(e)}.'
                        archive_entity.add_error('ingest_archiver.convert.error', msg, {
                            'data': json.dumps(archive_entity.data),
                            'error': str(e)
                        })
                entities.append(archive_entity)
            print("")

        return entities

    # TODO save notification to file for now, should be sending to rabbit mq in the future
    def notify_file_archiver(self, archive_submission: DspSubmission) -> []:
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

                    "submission_url": archive_submission.get_url(),
                    "files": files,
                    "manifest_id": entity.manifest_id
                }
                manifest = self.ingest_api.get_manifest_by_id(entity.manifest_id)
                if manifest.get('bundleUuid'):
                    message["dcp_bundle_uuid"] = manifest['bundleUuid']

                if protocols.is_10x(self.ontology_api, data.get("library_preparation_protocol")):
                    file_name = data['manifest_id']
                    if "lane_index" in entity.data:
                        file_name = f"{file_name}_{entity.data.get('lane_index')}"
                    file_name = f"{file_name}.bam"
                    message["conversion"] = {}
                    message["conversion"]["output_name"] = file_name
                    message["conversion"]["inputs"] = files
                    message["conversion"]["schema"] = protocols.map_10x_bam_schema(self.ontology_api, data.get(
                        "library_preparation_protocol"))
                    message["files"] = [{"name": file_name}]

                messages.append(message)

        archive_submission.file_upload_info = messages
        return messages
