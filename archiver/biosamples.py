from copy import deepcopy

from archiver.dsp_post_process import dsp_attribute, fixed_dsp_attribute, taxon_id, dsp_ontology
from jsonconverter.json_mapper import JsonMapper
from jsonconverter.post_process import format_date, default_to


def _taxon(*args):
    ontology_item = args[0]
    if ontology_item:
        genus_species = ontology_item[0]
        return genus_species.get('ontology_label')


def derive_concrete_type(*args):
    schema_url = args[0]
    concrete_type = get_concrete_type(schema_url)
    return dsp_attribute(concrete_type)


def get_concrete_type(schema_url):
    concrete_type = schema_url.split('/')[-1]
    return concrete_type


spec = {
    'alias': ['biomaterial.uuid.uuid'],
    'attributes': {
        'Biomaterial Core - Biomaterial Id': ['biomaterial.content.biomaterial_core.biomaterial_id', dsp_attribute],
        'HCA Biomaterial Type': ['biomaterial.content.describedBy', derive_concrete_type],
        'HCA Biomaterial UUID': ['biomaterial.uuid.uuid', dsp_attribute],
        'Is Living': ['biomaterial.content.is_living', dsp_attribute],
        'Medical History - Smoking History': ['biomaterial.content.medical_history.smoking_history', dsp_attribute],
        'Sex': ['biomaterial.content.sex', dsp_attribute],
        'project': ['', fixed_dsp_attribute, 'Human Cell Atlas']
    },
    'description': ['biomaterial.content.biomaterial_core.biomaterial_description'],
    'releaseDate': ['project.releaseDate', format_date],
    # this is to work around this being constantly empty
    'sampleRelationships': ['biomaterial.sampleRelationships', default_to, []],
    'taxon': ['biomaterial.content.genus_species', _taxon],
    'taxonId': ['biomaterial.content.biomaterial_core.ncbi_taxon_id', taxon_id],
    'title': ['biomaterial.content.biomaterial_core.biomaterial_name']
}


def convert(hca_data: dict):
    use_spec = deepcopy(spec)
    is_specimen = ('describedBy' in hca_data.get('biomaterial', {}).get('content',{}) and
                   get_concrete_type(hca_data['biomaterial']['content']['describedBy']) == 'specimen_from_organism')

    if 'releaseDate' not in hca_data.get('project', {}):
        use_spec['releaseDate'] = ['biomaterial.submissionDate', format_date]

    if is_specimen and 'organ' in hca_data['biomaterial']['content']:
        use_spec['attributes']['Organ'] = ['biomaterial.content.organ', dsp_ontology]

    converted_data = JsonMapper(hca_data).map(use_spec)

    if is_specimen and 'organ_parts' in hca_data['biomaterial']['content']:
        organ_parts = hca_data['biomaterial']['content']['organ_parts']
        if len(organ_parts) == 1:
            converted_data['attributes']['Organ Part'] = dsp_ontology(organ_parts[0])
        elif len(organ_parts) > 1:
            for index, organ_part in enumerate(organ_parts):
                converted_data['attributes'][f'Organ Part - {index}'] = dsp_ontology(organ_parts[index])

    return converted_data
