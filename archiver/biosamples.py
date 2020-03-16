from archiver.dsp_post_process import dsp_attribute, fixed_dsp_attribute
from conversion.json_mapper import JsonMapper
from conversion.post_process import format_date, default_to


def _taxon(*args):
    ontology_item = args[0]
    genus_species = ontology_item[0]
    return genus_species.get('ontology_label')


def _taxon_id(*args):
    taxon_ids = args[0]
    return taxon_ids[0] if taxon_ids and len(taxon_ids) > 0 else None


def derive_concrete_type(*args):
    schema_url = args[0]
    concrete_type = schema_url.split('/')[-1]
    return dsp_attribute(concrete_type)


spec = {
    '$on': 'biomaterial',
    'alias': ['uuid.uuid'],
    'attributes': {
        'Biomaterial Core - Biomaterial Id': ['content.biomaterial_core.biomaterial_id', dsp_attribute],
        'HCA Biomaterial Type': ['content.describedBy', derive_concrete_type],
        'HCA Biomaterial UUID': ['uuid.uuid', dsp_attribute],
        'Is Living': ['content.is_living', dsp_attribute],
        'Medical History - Smoking History': ['content.medical_history.smoking_history', dsp_attribute],
        'Sex': ['content.sex', dsp_attribute],
        'project': ['', fixed_dsp_attribute, 'Human Cell Atlas']
    },
    'description': ['content.biomaterial_core.biomaterial_description'],
    'releaseDate': ['submissionDate', format_date],
    # this is to work around this being constantly empty
    'sampleRelationships': ['sampleRelationships', default_to, []],
    'taxon': ['content.genus_species', _taxon],
    'taxonId': ['content.biomaterial_core.ncbi_taxon_id', _taxon_id],
    'title': ['content.biomaterial_core.biomaterial_name']
}


def convert(hca_data: dict):
    return JsonMapper(hca_data).map(spec)
