from api import ontology
from archiver.dsp_post_process import dsp_attribute, fixed_dsp_attribute, dsp_ontology
from archiver.instrument_model import to_dsp_name
from json_converter.json_mapper import JsonMapper, json_array, json_object

_ontology_api = ontology.__api__

_primer_mapping = {
    'poly-dT': 'Oligo-dT',
    'random': 'RANDOM'
}


def map_primer(*args):
    primer = str(args[0])
    mapping = _primer_mapping.get(primer)
    return dsp_attribute(mapping)


def library_layout_attribute(*args):
    paired_end = args[0]
    value = 'PAIRED' if paired_end else 'SINGLE'
    return dsp_attribute(value)


def taxon_id_attribute(*args):
    ids: list = args[0]
    return dsp_attribute(ids[0])


def nominal_value(*args):
    value = args[0]
    if value:
        value = str(args[0])
    else:
        value = "0"
    return dsp_attribute(value)


def instrument_model(*args):
    hca_name = args[0]
    return dsp_attribute(to_dsp_name(hca_name))


def convert(hca_data: dict):
    # added these for easier typing
    sp = 'sequencing_protocol'
    lp = 'library_preparation_protocol'
    ib = 'input_biomaterial'
    spec = {
        'alias': [f'{sp}.content.protocol_core.protocol_id'],
        'title': [f'{sp}.content.protocol_core.protocol_name'],
        'description': [f'{sp}.content.protocol_core.protocol_description'],
        'sampleUses': json_array(
            {
                'sampleRef': {
                    'alias': '{sampleAlias.placeholder}'
                }
            }
        ),
        'studyRef': json_object({'alias': '{studyAlias.placeholder}'}),
        'attributes': {
            'HCA Input Biomaterial UUID': [f'{ib}.uuid.uuid', dsp_attribute],
            'HCA Library Preparation Protocol UUID': [f'{lp}.uuid.uuid', dsp_attribute],
            'HCA Process UUID': ['process.uuid.uuid', dsp_attribute],
            'HCA Sequencing Protocol UUID': [f'{sp}.uuid.uuid', dsp_attribute],
            'Input Biomaterial - Biomaterial Core - Biomaterial Id':
                [f'{ib}.content.biomaterial_core.biomaterial_id', dsp_attribute],
            'Input Biomaterial - Biomaterial Core - Ncbi Taxon Id - 0':
                [f'{ib}.content.biomaterial_core.ncbi_taxon_id', taxon_id_attribute],
            'Library Preparation Protocol - End Bias': [f'{lp}.content.end_bias', dsp_attribute],
            'Library Preparation Protocol - Library Construction Method':
                [f'{lp}.content.library_construction_method', dsp_ontology],
            'Library Preparation Protocol - Nucleic Acid Source':
                [f'{lp}.content.nucleic_acid_source', dsp_attribute],
            'Library Preparation Protocol - Primer': [f'{lp}.content.primer', dsp_attribute],
            'Library Preparation Protocol - Protocol Core - Protocol Id':
                [f'{lp}.content.protocol_core.protocol_id', dsp_attribute],
            'Library Preparation Protocol - Strand': [f'{lp}.content.strand', dsp_attribute],
            'Process - Process Core - Process Id': ['process.content.process_core.process_id', dsp_attribute],
            'Sequencing Protocol - Paired End': [f'{sp}.content.paired_end', dsp_attribute],
            'Sequencing Protocol - Protocol Core - Protocol Id':
                [f'{sp}.content.protocol_core.protocol_id', dsp_attribute],
            'Sequencing Protocol - Sequencing Approach': [f'{sp}.content.sequencing_approach', dsp_ontology],
            'library_strategy': ['', fixed_dsp_attribute, 'OTHER'],
            'library_source': ['', fixed_dsp_attribute, 'TRANSCRIPTOMIC SINGLE CELL'],
            'library_selection': [f'{lp}.content.primer', map_primer],
            'library_layout': [f'{sp}.content.paired_end', library_layout_attribute],
            'library_name': [f'{ib}.content.biomaterial_core.biomaterial_id', dsp_attribute],
            'instrument_model': [f'{sp}.content.instrument_manufacturer_model.text', instrument_model],
            'platform_type': ['', fixed_dsp_attribute, 'ILLUMINA'],
            'design_description': ['', fixed_dsp_attribute, 'unspecified'],
            # TODO if library_layout is SINGLE, this is "0"
            'nominal_length': [f'{lp}.content.nominal_length', nominal_value],
            'nominal_sdev': [f'{lp}.content.nominal_sdev', nominal_value]
        }
    }

    return JsonMapper(hca_data).map(spec)
