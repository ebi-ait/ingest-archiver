from api.ingest import IngestAPI
from utils.graph import Graph
from .manifest import Manifest
from .entity import IngestArchiveEntity


class ArchiveEntityAggregator:
    def __init__(self, manifest: Manifest, ingest_api: IngestAPI, alias_prefix: str):
        self.manifest = manifest
        self.alias_prefix = alias_prefix
        self.ingest_api = ingest_api

    def _get_projects(self):
        project = self.manifest.get_project()
        if not project:
            return []
        archive_entity = IngestArchiveEntity()
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
        archive_entity = IngestArchiveEntity()
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
            archive_entity = IngestArchiveEntity()
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

                sample_links = []
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

        archive_entity = IngestArchiveEntity()
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

        links = {
            'studyRef': {
                "alias": self.generate_archive_entity_id('study', self.manifest.get_project())
            },
            'sampleUses': []
        }
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

            archive_entity = IngestArchiveEntity()
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
