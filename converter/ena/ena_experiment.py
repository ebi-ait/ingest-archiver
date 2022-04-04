from converter.ena.classes import AttributeType
from converter.ena.classes.sra_common import PlatformType, RefObjectType, TypeIlluminaModel
from converter.ena.classes.sra_experiment import Experiment, ExperimentSet, LibraryDescriptorType, LibraryType, SampleDescriptorType, TypeLibrarySelection, TypeLibrarySource, TypeLibraryStrategy
from converter.ena.base import EnaModel, XMLType
from converter.ena.ena_receipt import EnaReceipt
import logging


class EnaExperiment(EnaModel):

    def __init__(self, study_ref):
        self.study_ref = study_ref

    def archive(self, assay):
        experiment = self.create(assay)
        input_xml = self.xml_str(experiment)
        receipt_xml = self.post(XMLType.EXPERIMENT, input_xml, update=True if experiment.accession else False)
        accessions = EnaReceipt(XMLType.EXPERIMENT, input_xml, receipt_xml).process_receipt()
        if accessions and len(accessions) == 1:
            return accessions[0]
        raise EnaArchiveException('Ena archive no accession returned.')

    def create_set(self, assays):
        experiment_set = ExperimentSet()
        for assay in assays:
            experiment_set.experiment.append(self.create(assay))

        return experiment_set

    def create(self, assay):

        sequencing_protocol = assay["sequencing_protocol"]
        library_preparation_protocol = assay["library_preparation_protocol"]
        input_biomaterials = assay["input_biomaterials"]

        experiment = Experiment()
        experiment.experiment_attributes = Experiment.ExperimentAttributes()

        protocol_desc = sequencing_protocol.get("content", {}).get("protocol_core", {}).get("protocol_description")
        if protocol_desc:
            experiment.experiment_attributes.experiment_attribute.append(AttributeType(tag="Description", value=protocol_desc))

        experiment_accession = self.get_experiment_accession(assay)
        if experiment_accession:
            experiment.accession = experiment_accession
        else:
            experiment.alias = sequencing_protocol["content"]["protocol_core"]["protocol_id"]
        experiment.title = sequencing_protocol["content"]["protocol_core"]["protocol_name"]

        experiment.design = LibraryType()
        experiment.design.library_descriptor = LibraryDescriptorType()
        experiment.design.library_descriptor.library_strategy = TypeLibraryStrategy.OTHER
        experiment.design.library_descriptor.library_source = TypeLibrarySource.TRANSCRIPTOMIC_SINGLE_CELL
        experiment.design.library_descriptor.library_selection = self.ena_library_selection(library_preparation_protocol)
        experiment.design.library_descriptor.library_layout = self.ena_library_layout(sequencing_protocol)
        experiment.design.design_description = ''

        library_name, sample_accession = self.ena_library_name_and_accession(input_biomaterials)
        experiment.design.library_descriptor.library_name = library_name

        experiment.design.sample_descriptor = SampleDescriptorType()
        experiment.design.sample_descriptor.accession = sample_accession

        experiment.study_ref = RefObjectType()
        experiment.study_ref.accession = self.study_ref

        experiment.platform = self.ena_platform_type(sequencing_protocol)
        return experiment

    def get_experiment_accession(self, assay):
        experiment_accession = None
        try:
            experiment_accession = assay["content"]["insdc_experiment"]["insdc_experiment_accession"]
        except KeyError:
            pass # not accessioned (i.e archived) yet.
        return experiment_accession


    def ena_library_name_and_accession(self, input_biomaterials):
        # unlikely to have multiple biomaterial inputs it is still possible, ena takes one accession only, so
        # use accepted ERS or SAM accession only.
        library_name = None
        sample_accession = None
        for input_biomaterial in input_biomaterials:
            biosamples_accession = input_biomaterial["content"]["biomaterial_core"]["biosamples_accession"]
            if biosamples_accession.startswith("ERS") or biosamples_accession.startswith("SAM"):
                sample_accession = biosamples_accession
                library_name = input_biomaterial["content"]["biomaterial_core"]["biomaterial_id"]
                break
        return library_name, sample_accession

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
            instrument_model = HcaEnaMapping.INSTRUMENT_MANUFACTURER_MODEL_MAPPING.get(instrument_manufacturer_model.lower(), None)
            if not instrument_model:
                instrument_manufacturer_model = sequencing_protocol["content"]["instrument_manufacturer_model"]["ontology_label"]
                instrument_model = HcaEnaMapping.INSTRUMENT_MANUFACTURER_MODEL_MAPPING.get(instrument_manufacturer_model.lower(), None)
            if not instrument_model:
                instrument_model = TypeIlluminaModel.UNSPECIFIED

            platform_type.illumina = PlatformType.Illumina()
            platform_type.illumina.instrument_model = instrument_model

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
