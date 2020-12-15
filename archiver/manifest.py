from typing import Iterator

from api.ingest import IngestAPI
from archiver.biomaterial import Biomaterial
from archiver.errors import ArchiverException


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

    def get_biomaterials(self) -> Iterator[Biomaterial]:
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

    def _init_biomaterials(self) -> Iterator[Biomaterial]:
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
        assay_protocols = self.ingest_api.get_related_entity(assay, 'protocols', 'protocols')
        protocol_by_type = {}
        for protocol in assay_protocols:
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
