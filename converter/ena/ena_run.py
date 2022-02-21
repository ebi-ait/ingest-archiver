import logging
from config import ENA_FTP_DIR
from converter.ena.classes import Run, RunType, FileFiletype, RunSet, AttributeType
from converter.ena.classes.sra_common import RefObjectType
from converter.ena.base import EnaModel


class EnaRun(EnaModel):

    FILE_CHECKSUM_METHOD = 'MD5'
    SEQUENCE_FILE_TYPES = ['fq', 'fastq', 'fq.gz', 'fastq.gz']

    def __init__(self, hca_data):
        self.logger = logging.getLogger(__name__)
        self.submission = hca_data.submission
        self.assays = hca_data.submission["assays"]

        self.ena_upload_area_path = f'{ENA_FTP_DIR}/{self.submission["uuid"]["uuid"]}/'

    def create_set(self):
        run_set = RunSet()
        for assay in self.assays:
            run_set.run.append(self.create(assay))

        return run_set

    def create(self, assay):

        sequencing_protocol = assay["sequencing_protocol"]
        #library_preparation_protocol = assay["library_preparation_protocol"]
        derived_files = assay["derived_files"]

        run = Run()
        run.run_attributes = Run.RunAttributes()
        run.run_attributes.run_attribute.append(AttributeType(tag="Description", value=sequencing_protocol["content"]["protocol_core"]["protocol_description"]))

        run.title = assay["content"]["process_core"]["process_id"]
        run.experiment_ref = RefObjectType()
        run.experiment_ref.accession = ''
        run.alias = assay["uuid"]["uuid"]

        run.data_block = RunType.DataBlock()
        run.data_block.files = RunType.DataBlock.Files()

        for index, derived_file in enumerate(derived_files):
            file = RunType.DataBlock.Files.File()
            file.filename = self.ena_upload_area_path + derived_file["content"]["file_core"]["file_name"]

            hca_file_format = derived_file["content"]["file_core"]["format"]
            if hca_file_format in EnaRun.SEQUENCE_FILE_TYPES:
                file.filetype = FileFiletype.FASTQ
            else:
                self.logger.error(f'Unexpected file format: {hca_file_format}')

            file.checksum_method = EnaRun.FILE_CHECKSUM_METHOD

            if 'archiveResult' in derived_file and 'md5' in derived_file["archiveResult"]:
                file.checksum = derived_file["archiveResult"]["md5"]
            else:
                file.checksum = 'MISSING_MD5'
                self.logger.warning(f'File has not been archived (no md5 generated)')

            run.data_block.files.file.append(file)

        return run
