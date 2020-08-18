import json
import logging
from typing import Iterator, Tuple, List

from api import ontology
from api.dsp import DataSubmissionPortal
from api.ingest import IngestAPI
from archiver.accessioner import Accessioner
from archiver.converter import ConversionError, SampleConverter, ProjectConverter, \
    SequencingExperimentConverter, SequencingRunConverter, StudyConverter
from archiver.ingest_tracker import IngestTracker
from archiver.submission import ArchiveEntityMap, ArchiveEntity, ArchiveSubmission
from utils import protocols
from utils.graph import Graph


def _print_same_line(string):
    print(f'\r{string}', end='')


class ArchiverException(Exception):
    """Base-class for all exceptions raised by this module."""


class Biomaterial:
    def __init__(self, data, derived_by_process=None, derived_with_protocols=None,
                 derived_from_biomaterials: List[dict] = None):
        self.data = data
        self.derived_by_process = derived_by_process
        self.derived_with_protocols = derived_with_protocols
        self.derived_from_biomaterials = derived_from_biomaterials if derived_from_biomaterials else None

    @classmethod
    def from_uuid(cls, ingest_api, biomaterial_uuid):
        data = ingest_api.get_biomaterial_by_uuid(biomaterial_uuid)

        derived_by_processes_count = ingest_api.get_related_entity_count(data, 'derivedByProcesses', 'processes')

        if derived_by_processes_count:
            derived_by_processes = ingest_api.get_related_entity(data, 'derivedByProcesses', 'processes')
            # A biomaterial derived from multiple processes is not even supported in the Spreadsheet Importer
            if derived_by_processes_count > 1:
                raise ArchiverException(
                    'A biomaterial derived from multiple processes is not supported yet for conversion.')

            derived_by_process = next(derived_by_processes)

            protocols = ingest_api.get_related_entity(derived_by_process, 'protocols', 'protocols')

            derived_with_protocols = {}
            for protocol in protocols:
                protocol_type = ingest_api.get_concrete_entity_type(protocol)
                if not derived_with_protocols.get(protocol_type):
                    derived_with_protocols[protocol_type] = []
                derived_with_protocols[protocol_type].append(protocol)

            input_biomaterials_count = ingest_api.get_related_entity_count(derived_by_process, 'inputBiomaterials',
                                                                           'biomaterials')

            if not input_biomaterials_count:
                raise ArchiverException('A biomaterial has been derived by a process with no input biomaterial')

            input_biomaterials = ingest_api.get_related_entity(derived_by_process, 'inputBiomaterials', 'biomaterials')

            if input_biomaterials_count > 1:
                raise ArchiverException(
                    'A biomaterial derived from multiple biomaterials is not supported yet for conversion.')

            derived_from_biomaterials = list(input_biomaterials)
            return cls(data, derived_by_process, derived_with_protocols, derived_from_biomaterials)
        else:
            return cls(data)


class Manifest:
    def __init__(self, ingest_api: IngestAPI, manifest_id: str):
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

    def get_biomaterials(self) -> Iterator['Biomaterial']:
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

    def _init_biomaterials(self) -> Iterator['Biomaterial']:
        for biomaterial_uuid in list(self.manifest['fileBiomaterialMap']):
            yield Biomaterial.from_uuid(self.ingest_api, biomaterial_uuid)

    def _init_assay_process(self):
        file_uuid = list(self.manifest['fileFilesMap'])[0]
        file = self.ingest_api.get_file_by_uuid(file_uuid)

        derived_by_processes_count = self.ingest_api.get_related_entity_count(file, 'derivedByProcesses', 'processes')
        if derived_by_processes_count:
            if derived_by_processes_count > 1:
                raise ArchiverException(f'Manifest {self.manifest_id} has many assay processes.')
            derived_by_processes = self.ingest_api.get_related_entity(file, 'derivedByProcesses', 'processes')
            return next(derived_by_processes)
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
            raise ArchiverException('There should be 1 library preparation protocol for the assay process.')

        if len(sequencing_protocols) != 1:
            raise ArchiverException('There should be 1 sequencing_protocol for the assay process.')

        self.library_preparation_protocol = library_preparation_protocols[0]
        self.sequencing_protocol = sequencing_protocols[0]

    def _init_input_biomaterial(self):
        assay = self.get_assay_process()

        input_biomaterials_count = self.ingest_api.get_related_entity_count(assay, 'inputBiomaterials', 'biomaterials')

        if not input_biomaterials_count:
            raise ArchiverException('No input biomaterial found to the assay process.')

        input_biomaterials = self.ingest_api.get_related_entity(assay, 'inputBiomaterials', 'biomaterials')
        # TODO get first for now, clarify if it's possible to have multiple and how to specify the links

        return next(input_biomaterials)


class IngestArchiver:
    def __init__(self, ingest_api: IngestAPI,
                 dsp_api: DataSubmissionPortal,
                 ontology_api=ontology.__api__,
                 exclude_types=None, alias_prefix=None, dsp_validation=True):

        self.logger = logging.getLogger(__name__)
        self.ingest_api = ingest_api
        self.exclude_types = exclude_types if exclude_types else []
        self.alias_prefix = f"{alias_prefix}_" if alias_prefix else ""
        self.ontology_api = ontology_api
        self.dsp_api = dsp_api
        self.dsp_validation = dsp_validation
        self.accessioner = Accessioner(self.ingest_api)
        self.ingest_tracker = IngestTracker(ingest_api=self.ingest_api)

        self.converter = {
            "project": ProjectConverter(ontology_api=ontology_api),
            "sample": SampleConverter(ontology_api=ontology_api),
            "study": StudyConverter(ontology_api=ontology_api),
            "sequencingRun": SequencingRunConverter(ontology_api=ontology_api),
            "sequencingExperiment": SequencingExperimentConverter(ontology_api=ontology_api)
        }

        self.converter['sample'].ingest_api = self.ingest_api

    def archive(self, entity_map: ArchiveEntityMap):
        archive_submission, _ = self.archive_metadata(entity_map)
        self.notify_file_archiver(archive_submission)
        archive_submission.validate_and_submit()
        return archive_submission

    def archive_metadata(self, entity_map: ArchiveEntityMap) -> Tuple[ArchiveSubmission, IngestTracker]:
        archive_submission = ArchiveSubmission(dsp_api=self.dsp_api)
        archive_submission.entity_map = entity_map

        converted_entities = entity_map.get_converted_entities()

        if converted_entities:
            archive_submission.converted_entities = converted_entities
            archive_submission.submission = self.dsp_api.create_submission()
            dsp_submission_url = archive_submission.get_url()
            archive_submission.dsp_url = dsp_submission_url
            archive_submission.dsp_uuid = dsp_submission_url.rsplit('/', 1)[-1]
            print(f"DSP SUBMISSION: {dsp_submission_url}")
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
        archive_submission = ArchiveSubmission(dsp_api=self.dsp_api, dsp_submission_url=dsp_submission_url)

        if entity_map:
            archive_submission.entity_map = entity_map
            archive_submission.converted_entities = list(archive_submission.entity_map.get_converted_entities())

        if archive_submission.status == 'Draft':
            archive_submission.validate_and_submit()
        elif archive_submission.status == 'Completed':
            archive_submission.is_completed = True

        archive_submission.process_result()
        self.ingest_tracker.update_entities(entity_map)
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
                _print_same_line(str(progress_ctr))

                converter = self.converter[archive_entity_type]

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

                    except ConversionError as e:
                        msg = f'An error occured converting data to a {archive_entity_type}: {str(e)}.'
                        archive_entity.add_error('ingest_archiver.convert.error', msg, {
                            'data': json.dumps(archive_entity.data),
                            'error': str(e)
                        })
                entities.append(archive_entity)
            print("")

        return entities

    # TODO save notification to file for now, should be sending to rabbit mq in the future
    def notify_file_archiver(self, archive_submission: ArchiveSubmission) -> []:
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


class ArchiveEntityAggregator:
    def __init__(self, manifest: Manifest, ingest_api: IngestAPI, alias_prefix: str):
        self.manifest = manifest
        self.alias_prefix = alias_prefix
        self.ingest_api = ingest_api

    def _get_projects(self):
        project = self.manifest.get_project()
        if not project:
            return []
        archive_entity = ArchiveEntity()
        archive_type = "project"
        archive_entity.archive_entity_type = archive_type
        archive_entity.id = self.generate_archive_entity_id(archive_type, project)
        archive_entity.data = {"project": project}
        archive_entity.metadata_uuids = [project['uuid']['uuid']]
        archive_entity.accessioned_metadata_uuids = [project['uuid']['uuid']]
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
        archive_entity.metadata_uuids = [project['uuid']['uuid']]
        archive_entity.accessioned_metadata_uuids = [project['uuid']['uuid']]
        archive_entity.links = {
            "projectRef": {
                "alias": self.generate_archive_entity_id('project', project)
            }
        }
        return [archive_entity]

    def _get_samples(self):
        samples_map = {}
        derived_from_graph = Graph()

        project = self.manifest.get_project()
        for biomaterial in self.manifest.get_biomaterials():
            archive_entity = ArchiveEntity()
            archive_entity.manifest_id = self.manifest.manifest_id
            archive_type = "sample"
            archive_entity.archive_entity_type = archive_type
            archive_entity.id = self.generate_archive_entity_id(archive_type, biomaterial.data)

            archive_entity.data = {
                'biomaterial': biomaterial.data,
                'project': project
            }

            archive_entity.metadata_uuids = [biomaterial.data['uuid']['uuid'], project['uuid']['uuid']]
            archive_entity.accessioned_metadata_uuids = [biomaterial.data['uuid']['uuid']]

            if biomaterial.derived_by_process:
                # TODO protocols will be needed for samples conversion
                # archive_entity.data.update(biomaterial.derived_with_protocols)

                sample_links: []

                for derived_from in biomaterial.derived_from_biomaterials:
                    derived_from_alias = self.generate_archive_entity_id('sample', derived_from)
                    derived_from_graph.add_edge(derived_from_alias, archive_entity.id)
                    sample_links.append({
                        'alias': derived_from_alias,
                        'relationshipNature': 'derived from'
                    })

                links = {'sampleRelationships': sample_links}
                archive_entity.links = links

            samples_map[archive_entity.id] = archive_entity

        sorted_samples = derived_from_graph.topological_sort()
        priority_samples = [samples_map.get(sample) for sample in sorted_samples if samples_map.get(sample)]
        orphan_samples = [samples_map.get(sample) for sample in samples_map.keys() if sample not in priority_samples]

        return priority_samples + orphan_samples

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

        lib_prep_protocol = self.manifest.get_library_preparation_protocol()
        seq_protocol = self.manifest.get_sequencing_protocol()

        archive_entity.data = {
            'process': process,
            'library_preparation_protocol': lib_prep_protocol,
            'sequencing_protocol': seq_protocol,
            'input_biomaterial': input_biomaterial
        }

        archive_entity.metadata_uuids = [
            lib_prep_protocol['uuid']['uuid'],
            seq_protocol['uuid']['uuid'],
            input_biomaterial['uuid']['uuid'],
            process['uuid']['uuid'],
        ]

        archive_entity.accessioned_metadata_uuids = [process['uuid']['uuid']]

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
        lib_prep_protocol = self.manifest.get_library_preparation_protocol()
        files = self.manifest.get_files()

        lanes = {}
        # Index files by lane index
        for file in files:
            lane_index = file.get('content').get('lane_index', 1)
            if lane_index not in lanes:
                lanes[lane_index] = []
            lanes[lane_index].append(file)

        archive_entities = []

        for lane_index in lanes.keys():
            lane_files = lanes.get(lane_index)

            archive_entity = ArchiveEntity()
            archive_entity.manifest_id = self.manifest.manifest_id
            archive_type = "sequencingRun"
            archive_entity.archive_entity_type = archive_type
            archive_entity.id = self.generate_archive_entity_id(archive_type, process)

            archive_entity.data = {
                'library_preparation_protocol': lib_prep_protocol,
                'process': process,
                'files': lane_files,
                'manifest_id': archive_entity.manifest_id
            }

            metadata_uuids = [
                lib_prep_protocol['uuid']['uuid'],
                process['uuid']['uuid']
            ]

            file_uuids = [f['uuid']['uuid'] for f in lane_files]

            metadata_uuids.extend(file_uuids)

            archive_entity.metadata_uuids = metadata_uuids
            archive_entity.accessioned_metadata_uuids = file_uuids

            archive_entity.links = {
                'assayRefs': [{
                    "alias": self.generate_archive_entity_id('sequencingExperiment', process)
                }]
            }
            if len(lanes) > 1:
                archive_entity.data['lane_index'] = lane_index
                archive_entity.id = f'{archive_entity.id}_{lane_index}'
            archive_entities.append(archive_entity)

        return archive_entities

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
