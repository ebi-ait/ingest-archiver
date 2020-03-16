from api import ontology
from archiver.dsp_post_process import dsp_attribute, fixed_dsp_attribute, taxon_id_attribute
from archiver.instrument_model import to_dsp_name
from conversion.json_mapper import JsonMapper, json_array, json_object
from conversion.post_process import prefix_with, default_to

PREFIX_STUDY = 'study_'

_ontology_api = ontology.__api__

_primer_mapping = {
    'poly-dT': 'Oligo-dT',
    'random': 'RANDOM'
}


def _map_primer(*args):
    primer = str(args[0])
    mapping = _primer_mapping.get(primer)
    return dsp_attribute(mapping)


def _library_layout_attribute(*args):
    paired_end = args[0]
    value = 'PAIRED' if paired_end else 'SINGLE'
    return dsp_attribute(value)


def ontology_term(*args):
    return [{
        'terms': [{'url': _ontology_api.expand_curie()}],
        'value': args[0]
    }]


def string_attribute(*args):
    return dsp_attribute(str(args[0]))


def instrument_model(*args):
    hca_name = args[0]
    return dsp_attribute(to_dsp_name(hca_name))


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
            [f'{lp}.content.library_construction_method.text', ontology_term],
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
        'Sequencing Protocol - Sequencing Approach': [f'{sp}.content.sequencing_approach.text', ontology_term],
        'library_strategy': ['', fixed_dsp_attribute, 'OTHER'],
        'library_source': ['', fixed_dsp_attribute, 'TRANSCRIPTOMIC SINGLE CELL'],
        'library_selection': [f'{lp}.content.primer', _map_primer],
        'library_layout': [f'{sp}.content.paired_end', _library_layout_attribute],
        'library_name': [f'{ib}.content.biomaterial_core.biomaterial_id', dsp_attribute],
        'instrument_model': [f'{sp}.content.instrument_manufacturer_model.text', instrument_model],
        'platform_type': ['', fixed_dsp_attribute, 'ILLUMINA'],
        'design_description': ['', fixed_dsp_attribute, 'unspecified'],
        'nominal_length': [f'{lp}.content.nominal_length', string_attribute],
        'nominal_sdev': [f'{lp}.content.nominal_sdev', string_attribute]
    }
}


def convert_sequencing_experiment(hca_data: dict):
    return JsonMapper(hca_data).map(spec)


study_spec = {
    '$on': 'project',
    'alias': ['uuid.uuid', prefix_with, (PREFIX_STUDY)],
    'attributes': {
        'HCA Project UUID': ['uuid.uuid', dsp_attribute],
        'Project Core - Project Short Name': ['content.project_core.project_short_name', dsp_attribute],
        'study_type': ['', fixed_dsp_attribute, 'Transcriptome Analysis'],
        'study_abstract': ['content.project_core.project_description', dsp_attribute],
    },
    'title': ['content.project_core.project_title'],
    'description': ['content.project_core.project_description'],
    'projectRef': {
        'alias': ['', default_to, '{projectAlias.placeholder}']
    }
}


def convert_study(hca_data: dict):
    return JsonMapper(hca_data).map(study_spec)