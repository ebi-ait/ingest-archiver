import sys
import logging
import functools
import requests
from converter.ena.classes.sra_common import IdentifierType, PlatformType, RefObjectType, TypeIlluminaModel
from converter.ena.classes.sra_experiment import Experiment, ExperimentType, LibraryDescriptorType, LibraryType, SampleDescriptorType, TypeLibrarySelection, TypeLibrarySource, TypeLibraryStrategy

from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig


#INGEST_API='https://api.ingest.archive.data.humancellatlas.org'
INGEST_API='http://localhost:8080'


class EnaExperiment:

    def __init__(self):
        hca_submission = HcaSubmission('76283647-9b00-4651-9224-18a4db2b7b29')
        self.submission = hca_submission.submission
        self.assays = hca_submission.submission["assays"]
        for assay in self.assays:
            self.create(assay)

    def create(self, assay):
        experiment = Experiment()
        experiment_attributes = Experiment.ExperimentAttributes()

        sequencing_protocol = assay["sequencing_protocol"]
        library_preparation_protocol = assay["library_preparation_protocol"]
        input_biomaterials = assay["input_biomaterials"]

        experiment.alias = sequencing_protocol["content"]["protocol_core"]["protocol_id"]
        experiment.title = sequencing_protocol["content"]["protocol_core"]["protocol_name"]
        experiment_attributes.__setattr__('description', sequencing_protocol["content"]["protocol_core"]["protocol_description"])

        experiment.design = LibraryType()
        experiment.design.library_descriptor = LibraryDescriptorType()
        experiment.design.library_descriptor.library_strategy = TypeLibraryStrategy.OTHER
        experiment.design.library_descriptor.library_source = TypeLibrarySource.TRANSCRIPTOMIC_SINGLE_CELL
        experiment.design.library_descriptor.library_selection = self.ena_library_selection(library_preparation_protocol)
        experiment.design.library_descriptor.library_layout = self.ena_library_layout(sequencing_protocol)
        experiment.design.design_description = ''
        experiment.design.library_descriptor.library_name = '' # self.input_biomaterial["content"]["biomaterial_core"]["biomaterial_id"]

        experiment.design.sample_descriptor = SampleDescriptorType()
        experiment.design.sample_descriptor.accession = '' # self.input_biomaterial["content"]["biomaterial_core"]["biosamples_accession"]

        experiment.study_ref = RefObjectType()
        experiment.study_ref.accession = self.submission["project"]["content"]["insdc_project_accessions"][0] if 'project' in self.submission else ''

        experiment.platform = self.ena_platform_type(sequencing_protocol)

        experiment.experiment_attributes = experiment_attributes

        config = SerializerConfig(pretty_print=True)
        serializer = XmlSerializer(config=config)
        print(serializer.render(experiment))

        print("--------------------")

    def ena_library_selection(self, library_preparation_protocol):
        if library_preparation_protocol["content"]["primer"]:
            return HcaEnaMapping.LIBRARY_SELECTION_MAPPING.get(library_preparation_protocol["content"]["primer"], None)

    def ena_library_layout(self, sequencing_protocol):
        library_layout = LibraryDescriptorType.LibraryLayout()
        if sequencing_protocol["content"]["paired_end"]:
            library_layout.paired = LibraryDescriptorType.LibraryLayout.Paired()
            library_layout.paired.nominal_length = 0
            library_layout.paired.nominal_sdev = 0
        else:
            library_layout.single = ''
        return library_layout

    def ena_platform_type(self, sequencing_protocol):
        platform_type = PlatformType()
        if sequencing_protocol["content"]["instrument_manufacturer_model"]:
            instrument_manufacturer_model = sequencing_protocol["content"]["instrument_manufacturer_model"]["text"]

            platform_type.illumina = PlatformType.Illumina()
            print(sequencing_protocol["content"]["instrument_manufacturer_model"])
            platform_type.illumina.instrument_model = HcaEnaMapping.INSTRUMENT_MANUFACTURER_MODEL_MAPPING.get(instrument_manufacturer_model.lower(), None)

        return platform_type


class HcaEnaMapping:

    # Library selection mappings
    LIBRARY_SELECTION_MAPPING = {
        "poly-dT": TypeLibrarySelection.OLIGO_D_T,
        "random": TypeLibrarySelection.RANDOM
    }

    # ENA Instrument Model and Platform Type Mappings
    INSTRUMENT_MANUFACTURER_MODEL_MAPPING = {
        'illumina genome analyzer': TypeIlluminaModel.ILLUMINA_GENOME_ANALYZER,
        'illumina genome analyzer ii': TypeIlluminaModel.ILLUMINA_GENOME_ANALYZER_II,
        'illumina genome analyzer iix': TypeIlluminaModel.ILLUMINA_GENOME_ANALYZER_IIX,
        'illumina hiseq 2500': TypeIlluminaModel.ILLUMINA_HI_SEQ_2500,
        'illumina hiseq 2000': TypeIlluminaModel.ILLUMINA_HI_SEQ_2000,
        'illumina hiseq 1500': TypeIlluminaModel.ILLUMINA_HI_SEQ_1500,
        'illumina hiseq 1000': TypeIlluminaModel.ILLUMINA_HI_SEQ_1000,
        'illumina miseq': TypeIlluminaModel.ILLUMINA_MI_SEQ,
        'illumina hiscansq': TypeIlluminaModel.ILLUMINA_HI_SCAN_SQ,
        'hiseq x ten': TypeIlluminaModel.HI_SEQ_X_TEN,
        'illumina hiseq x 10': TypeIlluminaModel.HI_SEQ_X_TEN,
        'nextseq 500': TypeIlluminaModel.NEXT_SEQ_500,
        'illumina nextseq 500': TypeIlluminaModel.NEXT_SEQ_500,
        'hiseq x five': TypeIlluminaModel.HI_SEQ_X_FIVE,
        'illumina hiseq 3000': TypeIlluminaModel.ILLUMINA_HI_SEQ_3000,
        'illumina hiseq 4000': TypeIlluminaModel.ILLUMINA_HI_SEQ_4000,
        'nextseq 550': TypeIlluminaModel.NEXT_SEQ_550,
        'illumina novaseq 6000': TypeIlluminaModel.ILLUMINA_NOVA_SEQ_6000,
    }

# get all submissions processes
# check has inputBiomaterials and derivedFiles and protocols = seq_
from typing import List
import json
def handle_exception(f):
    @functools.wraps(f)
    def error(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except KeyError as e:
            logging.error(f'KeyError: source entity does not contain key: {str(e)}')
        except Exception as e:
            logging.error(f'HcaSubmission exception: {str(e)}')
    return error

class HcaSubmission:
    """
    Assay:
    [Biomaterial]  --> |   Process  |  -->  [File]
                       |     |      |
                       |     v      |
                       | [Protocol] |
    "submission": {
        ...
        "project": ...
        "assays": [
            {
                ... # process
                "sequencing_protocol": {...},
                "library_preparation_protocol": {...},
                "input_biomaterials": [...],
                "derived_files": [...]
            },
            ...
        ]
    }
    """
    session = requests.Session()
    # headers = {
    #     'Content-type': 'application/json',
    #     'Authorization': 'Bearer eyJraWQiOiJyc2ExIiwidHlwIjoiSldUIiwiYWxnIjoiUlMyNTYifQ.eyJzdWIiOiI2NWRmMDc3YzdjYzZmYTZmYThiMjEzZTI3MjBlMGU5ZmZkMzExNGNiQGVsaXhpci1ldXJvcGUub3JnIiwiYXpwIjoiZTIwNDFjMmQtOTQ0OS00NDY4LTg1NmUtZTg0NzExY2ViZDIxIiwic2NvcGUiOiJlbWFpbCBvcGVuaWQgcHJvZmlsZSIsImlzcyI6Imh0dHBzOlwvXC9sb2dpbi5lbGl4aXItY3plY2gub3JnXC9vaWRjXC8iLCJleHAiOjE2NDM5ODI5MjAsImlhdCI6MTY0Mzk2ODUyMCwianRpIjoiZDEyMDA4ZmItM2RkOS00NTJiLTk1NjgtNTk2OWU5NzJiMjZhIn0.oi0QGpfdXKYXbQvWCegfA6vgo6m8RbemAdGhty2tu25xSI0A2iYrM1rLAWXaoiu9I7JbcUHcWv9J1oPuCqGArYyXID86_3AoT8pmBPCEbj1E8nDhqoIj8M-UgRShuPta2TI7GkEXAbnpemhUealzxa90G-beuVLZ65LxGkDw5n6x2vnLyMj0lpq1aHHarZI9VtrYWRMOYEKCbW4UpjkgHiHFcIzAhgS8Ql83xX66ULTzADZNtzddN_OEQXCkVu0jmXn27xY6Sq-q818MuIRkLPGwtugPnvHZPOdR8VgxP3iU6C8FrMQB7RfoBYEAPFe1KF8qjmGiACHSyZQAOk54rw'
    # }
    headers = { 'Content-type': 'application/json' }

    def __init__(self, uuid):
        self.logger = logging.getLogger(__name__)
        self.uuid = uuid
        self.get_submission()

    @handle_exception
    def get_submission(self):
        url = f'{INGEST_API}/submissionEnvelopes/search/findByUuidUuid?uuid={self.uuid}'
        response = self.session.get(url, headers=self.headers)
        self.submission = None

        if response.ok:
            self.submission = response.json()

            # get project
            projects = self.get_submission_entities('projects')
            if projects:
                if len(projects) == 1:
                    self.submission["project"] = projects[0]
                    self.logger.info(f'Project UUID {self.submission["project"]["uuid"]["uuid"]}.')
                else:
                    self.logger.info(f'Multiple projects linked to submission {self.uuid}.')
            else:
                self.logger.info(f'No project linked to submission {self.uuid}. Sequencing Experiment requires a study accession.')

        self.get_assays()

    def get_assays(self):
        assays = []
        # get processes
        processes = self.get_submission_entities('processes')
        num_processes = len(processes)
        self.logger.info(f'{num_processes} processes in submission.')

        for index, process in enumerate(processes):

            self.logger.info(f"{index+1}/{num_processes} Checking {process['content']['process_core']['process_id']}")

            protocols = self.get_all_entities(process["_links"]["protocols"]["href"], 'protocols', [])
            sequencing_protocol = None
            library_preparation_protocol = None

            for protocol in protocols:
               described_by = protocol["content"]["describedBy"]
               if described_by.endswith('sequencing_protocol'):
                   sequencing_protocol = protocol
               elif described_by.endswith('library_preparation_protocol'):
                   library_preparation_protocol = protocol

            if sequencing_protocol or library_preparation_protocol:
                self.logger.info(f'Process has sequencing and library preparation protocols.')
                process["sequencing_protocol"] = sequencing_protocol
                process["library_preparation_protocol"] = library_preparation_protocol
            else:
                self.logger.info(f'No sequencing and library preparation protocols found.')
                continue

            # get input biomaterials
            input_biomaterials = self.get_all_entities(process["_links"]["inputBiomaterials"]["href"], 'biomaterials', [])

            if input_biomaterials:
                self.logger.info(f'Process has input biomaterials.')
                process["input_biomaterials"] = input_biomaterials
            else:
                self.logger.info(f'No input biomaterials found.')
                continue

            # get derived files
            derived_files = self.get_all_entities(process["_links"]["derivedFiles"]["href"], 'files', [])

            if derived_files:
                self.logger.info(f'Process has derived files.')
                process["derived_files"] = derived_files
            else:
                self.logger.info(f'No derived files found.')
                continue

            # rule out unexpected in/output
            derived_biomaterials = self.get_all_entities(process["_links"]["derivedBiomaterials"]["href"], 'biomaterials', [])
            if derived_biomaterials:
                self.logger.info('Process has derived biomaterials.')
                continue

            input_files = self.get_all_entities(process["_links"]["inputFiles"]["href"], 'files', [])
            if input_files:
                self.logger.info('Process has input files')
                continue

            if process["sequencing_protocol"] and process["library_preparation_protocol"] and process["input_biomaterials"] and process["derived_files"]:
                assays.append(process)

        self.logger.info(f'{len(assays)} assay processes found.')
        self.submission["assays"] = assays

    def get_submission_entities(self, entity_type):
        if self.submission:
            url = self.get_link(self.submission, entity_type)
            if url:
                return self.get_all_entities(url, entity_type, [])
        return []

    def get_link(self, json, entity):
        try:
            return json["_links"][entity]["href"]
        except KeyError:
            return None

    def get_all_entities(self, url, entity_type, entities=[]):
        response = self.session.get(url, headers=self.headers)
        response.raise_for_status()
        if "_embedded" in response.json():
            entities += response.json()["_embedded"][entity_type]

            if "next" in  response.json()["_links"]:
                url = response.json()["_links"]["next"]["href"]
                self.get_all_entities(url, entity_type, entities)
        return entities


format = ' %(asctime)s  - %(name)s - %(levelname)s in %(filename)s:' \
         '%(lineno)s %(funcName)s(): %(message)s'
logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                    format=format)

if __name__ == "__main__":
    #sub = HcaSubmission('8f44d9bb-527c-4d1d-b259-ee9ac62e11b6')
    #sub = HcaSubmission('76283647-9b00-4651-9224-18a4db2b7b29')
    EnaExperiment()

    #config = SerializerConfig(pretty_print=True)
    #serializer = XmlSerializer(config=config)
    #print(serializer.render(exp))