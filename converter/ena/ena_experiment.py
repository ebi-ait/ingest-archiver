from converter.ena.classes import AttributeType
from converter.ena.classes.sra_common import PlatformType, RefObjectType, TypeIlluminaModel
from converter.ena.classes.sra_experiment import Experiment, ExperimentSet, LibraryDescriptorType, LibraryType, SampleDescriptorType, TypeLibrarySelection, TypeLibrarySource, TypeLibraryStrategy


class EnaExperiment:

    def __init__(self, hca_data):
        self.submission = hca_data.submission
        self.assays = hca_data.submission["assays"]

    def experiment_set(self):
        experiment_set = ExperimentSet()
        for assay in self.assays:
            experiment_set.experiment.append(self.experiment(assay))

        return experiment_set

    def experiment(self, assay):

        sequencing_protocol = assay["sequencing_protocol"]
        library_preparation_protocol = assay["library_preparation_protocol"]
        input_biomaterials = assay["input_biomaterials"]

        experiment = Experiment()
        experiment.experiment_attributes = Experiment.ExperimentAttributes()
        experiment.experiment_attributes.experiment_attribute.append(AttributeType(tag="Description", value=sequencing_protocol["content"]["protocol_core"]["protocol_description"]))

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
        experiment.study_ref.accession = self.submission["project"]["content"]["insdc_project_accessions"][0] if 'project' in self.submission else ''

        experiment.platform = self.ena_platform_type(sequencing_protocol)
        return experiment

    def ena_library_name_and_accession(self, input_biomaterials):
        library_name = ""
        sample_accession = ""
        sep = ", "
        for input_biomaterial in input_biomaterials:
            library_name += input_biomaterial["content"]["biomaterial_core"]["biomaterial_id"] + sep
            sample_accession += input_biomaterial["content"]["biomaterial_core"]["biosamples_accession"] + sep

        library_name = library_name.rsplit(sep, 1)[0] if library_name.endswith(sep) else library_name
        sample_accession = sample_accession.rsplit(sep, 1)[0] if sample_accession.endswith(sep) else sample_accession

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

            platform_type.illumina = PlatformType.Illumina()
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
