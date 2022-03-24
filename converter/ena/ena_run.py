import logging
from converter.ena.classes import Run, RunType, FileFiletype, RunSet, AttributeType
from converter.ena.classes.sra_common import RefObjectType
from converter.ena.base import EnaModel, XMLType, EnaArchiveException
from converter.ena.ena_receipt import EnaReceipt


class EnaRun(EnaModel):

    FILE_CHECKSUM_METHOD = 'MD5'
    SEQUENCE_FILE_TYPES = ['fq', 'fastq', 'fq.gz', 'fastq.gz']

    def __init__(self, experiment_ref):
        self.experiment_ref = experiment_ref

    # Todo: extract function to parent class
    def archive(self, assay):
        run = self.create(assay)
        input_xml = self.xml_str(run)
        receipt_xml = self.post(XMLType.RUN, input_xml, update=True if run.accession else False)
        accessions = EnaReceipt(XMLType.RUN, input_xml, receipt_xml).process_receipt()
        if accessions and len(accessions) == 1:
            return accessions[0]
        raise EnaArchiveException('Ena archive no accession returned.')

    def create_set(self, assays):
        run_set = RunSet()
        for assay in assays:
            run_set.run.append(self.create(assay))

        return run_set

    def create(self, assay):

        sequencing_protocol = assay["sequencing_protocol"]
        derived_files = assay["derived_files"]

        run = Run()
        run.run_attributes = Run.RunAttributes()
        run.run_attributes.run_attribute.append(AttributeType(tag="Description", value=sequencing_protocol["content"]["protocol_core"]["protocol_description"]))

        run.title = assay["content"]["process_core"]["process_id"]
        self.__add_experiment_ref(run, assay)
        self.__add_run_accession_or_alias(run, assay)

        run.data_block = RunType.DataBlock()
        run.data_block.files = RunType.DataBlock.Files()

        for index, derived_file in enumerate(derived_files):
            if "fileArchiveResult" in derived_file and derived_file["fileArchiveResult"]:
                self.__add_run_file(run, derived_file)
            else:
                raise Exception('Data file has not been archived yet.')

        return run

    def __add_run_file(self, run, derived_file):
        if derived_file["fileArchiveResult"]["error"]:
            raise Exception('Data file archive error.')

        file = RunType.DataBlock.Files.File()
        file.filename = derived_file["fileArchiveResult"][
            "enaUploadPath"]  # derived_file["content"]["file_core"]["file_name"]

        hca_file_format = derived_file["content"]["file_core"]["format"]
        if hca_file_format in EnaRun.SEQUENCE_FILE_TYPES:
            file.filetype = FileFiletype.FASTQ
        else:
            raise Exception(f'Unexpected file format: {hca_file_format}')

        file.checksum_method = EnaRun.FILE_CHECKSUM_METHOD
        file.checksum = derived_file["fileArchiveResult"]["md5"]

        run.data_block.files.file.append(file)

    def __add_experiment_ref(self, run, assay):
        run.experiment_ref = RefObjectType()
        # If the run is submitted at the same time as the experiment then the accession attribute can’t be used to refer
        # to the experiment as the experiment accession has not been assigned yet.
        if self.experiment_ref:
            run.experiment_ref.accession = self.experiment_ref
        else:
            run.experiment_ref.refname = assay["sequencing_protocol"]["content"]["protocol_core"]["protocol_id"] # used as experiment alias

    def __add_run_accession_or_alias(self, run, assay):
        run_accession = self.__get_run_accession(assay)
        if run_accession:
            run.accession = run_accession
        else:
            run.alias = assay["sequencing_protocol"]["content"]["protocol_core"]["protocol_id"] #assay["uuid"]["uuid"]

    def __get_run_accession(self, assay):
        try:
            for derived_file in assay["derived_files"]:
                run_accessions = derived_file["content"]["insdc_run_accessions"]
                for acc in run_accessions:
                    if acc.startswith('ERR'):
                        return acc
        except KeyError:
            logging.debug("No ERR accession. File is not archived.")
        return None