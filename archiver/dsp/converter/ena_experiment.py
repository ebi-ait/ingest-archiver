from collections import namedtuple

from conversion.json_mapper import json_array, json_object
from .abstracts import DspOntologyConverter


class EnaExperimentConverter(DspOntologyConverter):
    def convert(self, hca_data):
        sp = 'sequencing_protocol'
        sp_c = 'sequencing_protocol.content'
        sp_core = 'sequencing_protocol.content.protocol_core'
        lp = 'library_preparation_protocol'
        lp_c = 'library_preparation_protocol.content'
        ib = 'input_biomaterial'
        ib_core = 'input_biomaterial.content.biomaterial_core'
        spec = {
            'alias': [f'{sp_core}.protocol_id'],
            'title': [f'{sp_core}.protocol_name'],
            'description': [f'{sp_core}.protocol_description'],
            'sampleUses': json_array(
                {
                    'sampleRef': {
                        'alias': '{sampleAlias.placeholder}'
                    }
                }
            ),
            'studyRef': json_object({'alias': '{studyAlias.placeholder}'}),
            'attributes': {
                'HCA Input Biomaterial UUID':
                    [f'{ib}.uuid.uuid', self.dsp_attribute],
                'HCA Library Preparation Protocol UUID':
                    [f'{lp}.uuid.uuid', self.dsp_attribute],
                'HCA Process UUID':
                    ['process.uuid.uuid', self.dsp_attribute],
                'HCA Sequencing Protocol UUID':
                    [f'{sp}.uuid.uuid', self.dsp_attribute],
                'Input Biomaterial - Biomaterial Core - Biomaterial Id':
                    [f'{ib_core}.biomaterial_id', self.dsp_attribute],
                'Input Biomaterial - Biomaterial Core - Ncbi Taxon Id - 0':
                    [f'{ib_core}.ncbi_taxon_id', self.taxon_id_attribute],
                'Library Preparation Protocol - End Bias':
                    [f'{lp_c}.end_bias', self.dsp_attribute],
                'Library Preparation Protocol - Library Construction Method':
                    [f'{lp_c}.library_construction_method', self.dsp_ontology],
                'Library Preparation Protocol - Nucleic Acid Source':
                    [f'{lp_c}.nucleic_acid_source', self.dsp_attribute],
                'Library Preparation Protocol - Primer':
                    [f'{lp_c}.primer', self.dsp_attribute],
                'Library Preparation Protocol - Protocol Core - Protocol Id':
                    [f'{lp_c}.protocol_core.protocol_id', self.dsp_attribute],
                'Library Preparation Protocol - Strand':
                    [f'{lp_c}.strand', self.dsp_attribute],
                'Process - Process Core - Process Id':
                    ['process.content.process_core.process_id', self.dsp_attribute],
                'Sequencing Protocol - Paired End':
                    [f'{sp_c}.paired_end', self.dsp_attribute],
                'Sequencing Protocol - Protocol Core - Protocol Id':
                    [f'{sp_core}.protocol_id', self.dsp_attribute],
                'Sequencing Protocol - Sequencing Approach':
                    [f'{sp_c}.sequencing_approach', self.dsp_ontology],
                'library_strategy': ['', self.fixed_dsp_attribute, 'OTHER'],
                'library_source': ['', self.fixed_dsp_attribute, 'TRANSCRIPTOMIC SINGLE CELL'],
                'library_selection': [f'{lp_c}.primer', self.map_primer],
                'library_layout': [f'{sp_c}.paired_end', self.library_layout_attribute],
                'library_name': [f'{ib_core}.biomaterial_id', self.dsp_attribute],
                'instrument_model':
                    [f'{sp_c}.instrument_manufacturer_model.text', self.instrument_model],
                'platform_type': ['', self.fixed_dsp_attribute, 'ILLUMINA'],
                'design_description': ['', self.fixed_dsp_attribute, 'unspecified'],
                # TODO if library_layout is SINGLE, this is "0"
                'nominal_length': [f'{lp_c}.nominal_length', self.nominal_value],
                'nominal_sdev': [f'{lp_c}.nominal_sdev', self.nominal_value]
            }
        }
        return self.map(hca_data, spec)
        
    @staticmethod
    def map_primer(*args):
        primer_mapping = {
            'poly-dT': 'Oligo-dT',
            'random': 'RANDOM'
        }
        primer = str(args[0])
        mapping = primer_mapping.get(primer)
        return DspOntologyConverter.dsp_attribute(mapping)

    @staticmethod
    def library_layout_attribute(*args):
        paired_end = args[0]
        value = 'PAIRED' if paired_end else 'SINGLE'
        return DspOntologyConverter.dsp_attribute(value)

    @staticmethod
    def nominal_value(*args):
        value = args[0]
        if value:
            value = str(args[0])
        else:
            value = "0"
        return DspOntologyConverter.dsp_attribute(value)

    @staticmethod
    def instrument_model(*args):
        hca_name = args[0]
        model_map = EnaExperimentConverter.prepare_map()
        instrument_model = model_map.get(hca_name.lower())
        dsp_model = instrument_model.dsp_name if instrument_model else 'unspecified'
        return DspOntologyConverter.dsp_attribute(dsp_model)

    @staticmethod
    def prepare_map():
        Synonym = namedtuple('Synonym', ['main', 'alternate'])
        model_names = ['Illumina Genome Analyzer', 'Illumina Genome Analyzer II',
                       'Illumina Genome Analyzer IIx',
                       'Illumina HiSeq 2500', 'Illumina HiSeq 2000', 'Illumina HiSeq 1500',
                       'Illumina HiSeq 1000',
                       'Illumina MiSeq', 'Illumina HiScanSQ', 'HiSeq X Ten', 'NextSeq 500',
                       'HiSeq X Five',
                       'Illumina HiSeq 3000', 'Illumina HiSeq 4000', 'NextSeq 550',
                       'Illumina NovaSeq 6000']
        instrument_models = [InstrumentModel.illumina(name) for name in model_names]
        model_map = {model.hca_name: model for model in instrument_models}

        synonyms = [Synonym('hiseq x ten', 'illumina hiseq x 10'),
                    Synonym('nextseq 500', 'illumina nextseq 500')]
        for synonym in synonyms:
            model_map[synonym.alternate] = model_map[synonym.main].hca_synonym(synonym.alternate)

        return model_map


class InstrumentModel:
    def __init__(self, hca_name: str = '', platform_type: str = '', dsp_name: str = ''):
        self.hca_name = hca_name
        self.platform_type = platform_type
        self.dsp_name = dsp_name

    def hca_synonym(self, hca_name: str):
        return InstrumentModel(hca_name, self.platform_type, self.dsp_name)

    @staticmethod
    def illumina(dsp_name: str):
        return InstrumentModel(dsp_name.lower(), 'ILLUMINA', dsp_name)
