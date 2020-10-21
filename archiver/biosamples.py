from copy import deepcopy

from archiver.dsp_post_process import dsp_attribute, fixed_dsp_attribute, taxon_id
from conversion.json_mapper import JsonMapper
from conversion.post_process import format_date, default_to


def _taxon(*args):
    ontology_item = args[0]
    if ontology_item:
        genus_species = ontology_item[0]
        return genus_species.get('ontology_label')


def derive_concrete_type(*args):
    schema_url = args[0]
    concrete_type = schema_url.split('/')[-1]
    return dsp_attribute(concrete_type)


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

    if 'releaseDate' not in hca_data.get('project', {}):
        use_spec['releaseDate'] = ['biomaterial.submissionDate', format_date]

    return JsonMapper(hca_data).map(use_spec)
