from api import ontology
from archiver.dsp_post_process import dsp_attribute, fixed_dsp_attribute, taxon_id_attribute, dsp_ontology
from archiver.instrument_model import to_dsp_name
from jsonconverter.json_mapper import JsonMapper, json_array, json_object
from jsonconverter.post_process import prefix_with, default_to, format_date
from utils import protocols

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


# added these for easier typing
sp = 'sequencing_protocol'
lp = 'library_preparation_protocol'
ib = 'input_biomaterial'
sq_experiment_spec = {
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
        'library_selection': [f'{lp}.content.primer', _map_primer],
        'library_layout': [f'{sp}.content.paired_end', _library_layout_attribute],
        'library_name': [f'{ib}.content.biomaterial_core.biomaterial_id', dsp_attribute],
        'instrument_model': [f'{sp}.content.instrument_manufacturer_model.text', instrument_model],
        'platform_type': ['', fixed_dsp_attribute, 'ILLUMINA'],
        'design_description': ['', fixed_dsp_attribute, 'unspecified'],
        # TODO if library_layout is SINGLE, this is "0"
        'nominal_length': [f'{lp}.content.nominal_length', nominal_value],
        'nominal_sdev': [f'{lp}.content.nominal_sdev', nominal_value]
    }
}


def convert_sequencing_experiment(hca_data: dict):
    return JsonMapper(hca_data).map(sq_experiment_spec)


study_spec = {
    '$on': 'project',
    'alias': ['uuid.uuid', prefix_with, PREFIX_STUDY],
    'attributes': {
        'HCA Project UUID': ['uuid.uuid', dsp_attribute],
        'Project Core - Project Short Name': ['content.project_core.project_short_name', dsp_attribute],
        'study_type': ['', fixed_dsp_attribute, 'Transcriptome Analysis'],
        'study_abstract': ['content.project_core.project_description', dsp_attribute],
    },
    'title': ['content.project_core.project_title'],
    'description': ['content.project_core.project_description'],
    'releaseDate': ['releaseDate', format_date],
    'projectRef': {
        'alias': ['', default_to, '{projectAlias.placeholder}']
    }
}


def convert_study(hca_data: dict):
    return JsonMapper(hca_data).map(study_spec)


_sq_run_alias_prefix = 'sequencingRun_'

_file_format_mapping = {
    'fastq.gz': 'fastq',
    'bam': 'bam',
    'cram': 'cram',
}


def _sq_run_assay_ref(*args):
    return [{'alias': prefix_with(args[0], _sq_run_alias_prefix)}]


def convert_sequencing_run(hca_data: dict):
    mapper = JsonMapper(hca_data)
    converted_data = mapper.map({
        '$on': 'process',
        # being overwritten 'alias': ['uuid.uuid', prefix_with, _sq_run_alias_prefix],
        'title': ['content.process_core.process_name', default_to, ''],
        'description': ['content.process_core.process_description', default_to, ''],
        # being overwritten 'assayRefs': ['uuid.uuid', _sq_run_assay_ref]
    })

    converted_files = mapper.map({
        '$on': 'files',
        'name': ['content.file_core.file_name'],
        'format': ['content.file_core.format'],
        'uuid': ['uuid.uuid'],
        'lane_index': ['content.lane_index'],
        'read_index': ['content.read_index']
    })

    converted_data['attributes'] = _sq_run_file_attributes(converted_files)
    converted_data['files'] = _sq_run_files(converted_files, hca_data)
    return converted_data


def _sq_run_file_attributes(converted_files):
    file_attributes = {}
    for index, file in enumerate(converted_files):
        file_attributes.update({
            f'Files - {index} - File Core - File Name': dsp_attribute(file.get('name')),
            f'Files - {index} - File Core - Format': dsp_attribute(file.get('format')),
            f'Files - {index} - HCA File UUID': dsp_attribute(file.get('uuid')),
            f'Files - {index} - Read Index': dsp_attribute(file.get('read_index')),
            f'Files - {index} - Lane Index': dsp_attribute(file.get('lane_index'))
        })
    return file_attributes


def _sq_run_files(converted_files, hca_data):
    if protocols.is_10x(_ontology_api, hca_data.get("library_preparation_protocol")):
        file_name = hca_data['manifest_id']
        if 'lane_index' in hca_data:
            file_name = f"{file_name}_{hca_data.get('lane_index')}"
        files = [{
            'name': f'{file_name}.bam',
            'type': 'bam'
        }]
    else:
        files = [{
            'name': file.get('name'),
            'type': _file_format_mapping.get(file.get('format'))
        } for file in converted_files]
    return files
