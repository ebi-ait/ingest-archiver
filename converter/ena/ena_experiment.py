import logging
import requests
from converter.ena.classes.sra_common import IdentifierType, PlatformType, RefObjectType, TypeIlluminaModel
from converter.ena.classes.sra_experiment import Experiment, ExperimentType, LibraryDescriptorType, LibraryType, SampleDescriptorType, TypeLibrarySelection, TypeLibrarySource, TypeLibraryStrategy

from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig


#INGEST_API='https://api.ingest.archive.data.humancellatlas.org'
INGEST_API='http://localhost:8080'


class EnaExperiment:

    def __init__(self, input_biomaterial, assay_process, lib_prep_protocol, sequencing_protocol, output_files):
        self.input_biomaterial = input_biomaterial
        self.assay_process = assay_process
        self.lib_prep_protocol = lib_prep_protocol
        self.sequencing_protocol = sequencing_protocol
        self.output_files = output_files

    def create(self):
        experiment = Experiment()
        experiment_attributes = Experiment.ExperimentAttributes()

        experiment.alias = self.sequencing_protocol["content"]["protocol_core"]["protocol_id"]
        experiment.title = self.sequencing_protocol["content"]["protocol_core"]["protocol_name"]
        experiment_attributes.__setattr__('description', self.sequencing_protocol["content"]["protocol_core"]["protocol_description"])

        experiment.design = LibraryType()
        experiment.design.library_descriptor = LibraryDescriptorType()
        experiment.design.library_descriptor.library_strategy = TypeLibraryStrategy.OTHER
        experiment.design.library_descriptor.library_source = TypeLibrarySource.TRANSCRIPTOMIC_SINGLE_CELL
        experiment.design.library_descriptor.library_selection = self.ena_library_selection()
        experiment.design.library_descriptor.library_layout = self.ena_library_layout()
        experiment.design.design_description = 'unspecified'
        experiment.design.library_descriptor.library_name = self.input_biomaterial["content"]["biomaterial_core"]["biomaterial_id"]

        experiment.design.sample_descriptor = SampleDescriptorType()
        experiment.design.sample_descriptor.accession = self.input_biomaterial["content"]["biomaterial_core"]["biosamples_accession"]

        experiment.study_ref = RefObjectType()
        experiment.study_ref.accession = self.project["content"]["insdc_project_accessions"][0]

        experiment.platform = self.ena_platform_type()

        experiment.experiment_attributes = experiment_attributes

    def ena_library_layout(self):
        library_layout = LibraryDescriptorType.LibraryLayout()
        if self.sequencing_protocol["content"]["paired_end"]:
            library_layout.paired = LibraryDescriptorType.LibraryLayout.Paired()
            library_layout.paired.nominal_length = 0
            library_layout.paired.nominal_sdev = 0
        else:
            library_layout.single = object()
        return library_layout

    def ena_library_selection(self):
        if self.lib_prep_protocol["content"]["primer"]:
            return HcaEnaMapping.LIBRARY_SELECTION_MAPPING.get(self.lib_prep_protocol["content"]["primer"], None)


    def ena_platform_type(self):
        platform_type = PlatformType()
        if self.sequencing_protocol["content"]["instrument_manufacturer_model"]:
            instrument_manufacturer_model = self.sequencing_protocol["content"]["instrument_manufacturer_model"]["text"]

            platform_type.illumina = PlatformType.Illumina()
            platform_type.illumina.instrument_model = HcaEnaMapping.INSTRUMENT_MANUFACTURER_MODEL_MAPPING.get(instrument_manufacturer_model, None)

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
        'nextseq 550': TypeIlluminaModel.NEXT_SEQ_550
    }

# get all submissions processes
# check has inputBiomaterials and derivedFiles and protocols = seq_

class HcaSubmission:
    submission: any
    project: any
    biomaterials: list
    processes: list
    protocols: list
    files: list

    session = requests.Session()
    # headers = {
    #     'Content-type': 'application/json',
    #     'Authorization': 'Bearer eyJraWQiOiJyc2ExIiwidHlwIjoiSldUIiwiYWxnIjoiUlMyNTYifQ.eyJzdWIiOiI2NWRmMDc3YzdjYzZmYTZmYThiMjEzZTI3MjBlMGU5ZmZkMzExNGNiQGVsaXhpci1ldXJvcGUub3JnIiwiYXpwIjoiZTIwNDFjMmQtOTQ0OS00NDY4LTg1NmUtZTg0NzExY2ViZDIxIiwic2NvcGUiOiJlbWFpbCBvcGVuaWQgcHJvZmlsZSIsImlzcyI6Imh0dHBzOlwvXC9sb2dpbi5lbGl4aXItY3plY2gub3JnXC9vaWRjXC8iLCJleHAiOjE2NDM5ODI5MjAsImlhdCI6MTY0Mzk2ODUyMCwianRpIjoiZDEyMDA4ZmItM2RkOS00NTJiLTk1NjgtNTk2OWU5NzJiMjZhIn0.oi0QGpfdXKYXbQvWCegfA6vgo6m8RbemAdGhty2tu25xSI0A2iYrM1rLAWXaoiu9I7JbcUHcWv9J1oPuCqGArYyXID86_3AoT8pmBPCEbj1E8nDhqoIj8M-UgRShuPta2TI7GkEXAbnpemhUealzxa90G-beuVLZ65LxGkDw5n6x2vnLyMj0lpq1aHHarZI9VtrYWRMOYEKCbW4UpjkgHiHFcIzAhgS8Ql83xX66ULTzADZNtzddN_OEQXCkVu0jmXn27xY6Sq-q818MuIRkLPGwtugPnvHZPOdR8VgxP3iU6C8FrMQB7RfoBYEAPFe1KF8qjmGiACHSyZQAOk54rw'
    # }
    headers = { 'Content-type': 'application/json' }

    def __init__(self, uuid):
        self.uuid = uuid
        self.get_submission()

    def get_submission(self):
        url = f'{INGEST_API}/submissionEnvelopes/search/findByUuidUuid?uuid={self.uuid}'
        response = self.session.get(url, headers=self.headers)
        self.submission = None

        assays = []

        if response.ok:
            self.submission = response.json()

            # get project

            # get protocols
            self.processes = self.get_entities('processes')
            for process in self.processes:
                print(process['content']['process_core']['process_id'])

                is_assay = True

                process["protocols"] = self.session.get(process["_links"]["protocols"]["href"], headers=self.headers).json()

                if '_embedded' in process["protocols"]:
                    correct_protocol = True
                    for protocol in process["protocols"]["_embedded"]["protocols"]:
                       described_by = protocol["content"]["describedBy"]
                       if described_by.endswith('sequencing_protocol') or described_by.endswith('library_preparation_protocol'):
                           continue
                       else:
                           is_assay = False

                if is_assay:
                    print(f"Has got sequencing / library preparation protocols")
                else:
                    print('Not assay process')
                    continue

                process["inputBiomaterials"] = self.session.get(process["_links"]["inputBiomaterials"]["href"], headers=self.headers).json()

                if '_embedded' in process["inputBiomaterials"] and len(process["inputBiomaterials"]["_embedded"]["biomaterials"]) > 0:
                    print('Has got input biomaterials')
                else:
                    print('Not assay process')
                    continue

                process["derivedFiles"] = self.session.get(process["_links"]["derivedFiles"]["href"], headers=self.headers).json()
                if '_embedded' in process["derivedFiles"] and len(process["derivedFiles"]["_embedded"]["files"]) > 0:
                    print('Has got derived files')
                else:
                    print('Not assay process')
                    continue

                process["derivedBiomaterials"] = self.session.get(process["_links"]["derivedBiomaterials"]["href"], headers=self.headers).json()
                if '_embedded' in process["derivedBiomaterials"] and len(
                        process["derivedBiomaterials"]["_embedded"]["biomaterials"]) > 0:
                    print('XXX Has got derived biomaterials')
                    is_assay = False

                process["inputFiles"] = self.session.get(process["_links"]["inputFiles"]["href"], headers=self.headers).json()
                if '_embedded' in process["inputFiles"] and len(
                        process["inputFiles"]["_embedded"]["files"]) > 0:
                    print('XXX Has got input files')
                    is_assay = False



                if is_assay:
                    assays.append(process)

            print(f"Number of assay processes: {len(assays)}")
            print(assays)



    def get_entities(self, entity_type):
        if self.submission:
            url = self.get_link(self.submission, entity_type)
            if url:
                return self._get_all(url, entity_type)
        return []

    def get_link(self, json, entity):
        try:
            return json["_links"][entity]["href"]
        except KeyError:
            return None

    def _get_all(self, url, entity_type):
        response = self.session.get(url, headers=self.headers)
        response.raise_for_status()
        if "_embedded" in response.json():
            for entity in response.json()["_embedded"][entity_type]:
                yield entity
            while "next" in response.json()["_links"]:
                r = self.session.get(response.json()["_links"]["next"]["href"], headers=self.headers)
                for entity in r.json()["_embedded"][entity_type]:
                    yield entity



if __name__ == "__main__":
    sub = HcaSubmission('76283647-9b00-4651-9224-18a4db2b7b29')

    #config = SerializerConfig(pretty_print=True)
    #serializer = XmlSerializer(config=config)
    #print(serializer.render(exp))