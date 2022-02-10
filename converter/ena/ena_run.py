import sys
import logging
import functools
import requests

from converter.ena.classes import Run, RunType, FileFiletype
from converter.ena.classes.sra_common import IdentifierType, PlatformType, RefObjectType, TypeIlluminaModel
from converter.ena.classes.sra_experiment import Experiment, ExperimentType, LibraryDescriptorType, LibraryType, SampleDescriptorType, TypeLibrarySelection, TypeLibrarySource, TypeLibraryStrategy

from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig


#INGEST_API='https://api.ingest.archive.data.humancellatlas.org'
INGEST_API='http://localhost:8080'


class EnaRun:

    FILE_CHECKSUM_METHOD = 'MD5'
    SEQUENCE_FILE_TYPES = ['fq', 'fastq', 'fq.gz', 'fastq.gz']

    def __init__(self, input_biomaterial, assay_process, lib_prep_protocol, sequencing_protocol, output_files):
        self.input_biomaterial = input_biomaterial
        self.assay_process = assay_process
        self.lib_prep_protocol = lib_prep_protocol
        self.sequencing_protocol = sequencing_protocol
        self.output_files = output_files

    def create(self):
        run = Run()
        run.title = self.assay_process["content"]["process_core"]["process_name"]
        run_attributes = Run.RunAttributes()
        run_attributes.__setattr__('description', self.assay_process["content"]["protocol_core"]["protocol_description"])
        run.experiment_ref = RefObjectType()
        run.experiment_ref.accession = ''
        run.alias = self.assay_process["content"]["uuid"]

        run.data_block = RunType.DataBlock()
        run.data_block.files = RunType.DataBlock.Files()
        file = RunType.DataBlock.Files.File()
        file.filename = output_file["file_core.file_name"]

        hca_file_format = output_file["file_core.file_format"]
        if hca_file_format in EnaRun.SEQUENCE_FILE_TYPES:
            file.filetype = FileFiletype.FASTQ
        else:
            error(f'Unexpected file format: {hca_file_format}')

        file.checksum_method = EnaRun.FILE_CHECKSUM_METHOD

        if output_file["archive.md5"]:
            file.checksum = output_file["archive.md5"]
        else:
            error(f'File has not been archived (no md5 generated)')

        file.__setattr__("Read Index", "content.read_index")
        file.__setattr__("HCA File UUID", "dataFileUuid")

        run.data_block.files.file.append()

        run.run_attributes = run_attributes
        pass