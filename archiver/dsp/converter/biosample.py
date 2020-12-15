from conversion.post_process import format_date, default_to
from .abstracts import DspOntologyConverter


class BiosampleConverter(DspOntologyConverter):
    def convert(self, hca_data):
        content = 'biomaterial.content'
        core = f'{content}.biomaterial_core'
        spec = {
            'alias': ['biomaterial.uuid.uuid'],
            'attributes': {
                'Biomaterial Core - Biomaterial Id': [f'{core}.biomaterial_id', self.dsp_attribute],
                'HCA Biomaterial Type': [f'{content}.describedBy', self.derive_concrete_type],
                'HCA Biomaterial UUID': ['biomaterial.uuid.uuid', self.dsp_attribute],
                'Is Living': [f'{content}.is_living', self.dsp_attribute],
                'Medical History - Smoking History': [f'{content}.medical_history.smoking_history',
                                                      self.dsp_attribute],
                'Sex': [f'{content}.sex', self.dsp_attribute],
                'project': ['', self.fixed_dsp_attribute, 'Human Cell Atlas']
            },
            'description': [f'{core}.biomaterial_description'],
            'releaseDate': ['project.releaseDate', format_date],
            # this is to work around this being constantly empty
            'sampleRelationships': ['biomaterial.sampleRelationships', default_to, []],
            'taxon': [f'{content}.genus_species', self.get_label],
            'taxonId': [f'{core}.ncbi_taxon_id', self.taxon_id],
            'title': [f'{core}.biomaterial_name']
        }
        is_specimen = self.adjust_spec_for_data(hca_data, spec)
        converted_data = self.map(hca_data, spec)
        if is_specimen and 'organ_parts' in hca_data['biomaterial']['content']:
            self.set_organ_part(converted_data, hca_data['biomaterial']['content']['organ_parts'])

        return converted_data

    def adjust_spec_for_data(self, hca_data, spec):
        schema_url = hca_data.get('biomaterial', {}).get('content', {}).get('describedBy', '')
        is_specimen = schema_url and self.get_concrete_type(schema_url) == 'specimen_from_organism'
        if not hca_data.get('project', {}).get('releaseDate', None):
            spec['releaseDate'] = ['biomaterial.submissionDate', format_date]
        if is_specimen and hca_data['biomaterial']['content'].get('organ', None):
            spec['attributes']['Organ'] = ['biomaterial.content.organ', self.dsp_ontology]
        return is_specimen

    def set_organ_part(self, data, organ_parts):
        if len(organ_parts) == 1:
            data['attributes']['Organ Part'] = self.dsp_ontology(organ_parts[0])
        elif len(organ_parts) > 1:
            for i, organ_part in enumerate(organ_parts):
                data['attributes'][f'Organ Part - {i}'] = self.dsp_ontology(organ_parts[i])

    @staticmethod
    def get_label(*args):
        ontology_item = args[0]
        if ontology_item:
            genus_species = ontology_item[0]
            return genus_species.get('ontology_label')

    @staticmethod
    def derive_concrete_type(*args):
        schema_url = args[0]
        concrete_type = BiosampleConverter.get_concrete_type(schema_url)
        return DspOntologyConverter.dsp_attribute(concrete_type)

    @staticmethod
    def get_concrete_type(schema_url):
        concrete_type = schema_url.split('/')[-1]
        return concrete_type
