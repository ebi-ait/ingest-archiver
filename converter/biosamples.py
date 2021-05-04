from biosamples_v4.models import Sample, Attribute
from json_converter.json_mapper import JsonMapper
from .errors import MissingBioSamplesDomain


def get_concrete_type(schema_url):
    concrete_type = schema_url.split('/')[-1]
    return concrete_type


ATTRIBUTE_SPEC = {
    'Biomaterial Core - Biomaterial Id': ['content.biomaterial_core.biomaterial_id'],
    'HCA Biomaterial Type': ['content.describedBy', get_concrete_type],
    'HCA Biomaterial UUID': ['uuid.uuid'],
    'Is Living': ['content.is_living'],
    'Medical History - Smoking History': ['content.medical_history.smoking_history'],
    'Sex': ['content.sex']
}


class BioSamplesConverter:
    def __init__(self, default_domain=None):
        self.default_domain = default_domain

    def convert(self, biomaterial: dict, domain: str = None, release_date: str = None, accession: str = None) -> Sample:
        if not domain and not self.default_domain:
            raise MissingBioSamplesDomain()
        biomaterial_content = biomaterial.get('content', {})
        biomaterial_core = biomaterial_content.get('biomaterial_core', {})
        sample = Sample(
            accession=accession if accession else biomaterial_core.get('biosamples_accession'),
            name=biomaterial_core.get('biomaterial_name'),
            update=biomaterial.get('updateDate'),
            domain=domain if domain else self.default_domain,
            species=biomaterial_content['genus_species'][0].get('ontology_label') if biomaterial_content.get('genus_species') else None,
            ncbi_taxon_id=biomaterial_core.get('ncbi_taxon_id')[0] if biomaterial_core.get('ncbi_taxon_id') else None,
            release=release_date if release_date else biomaterial.get('submissionDate')
        )
        sample._append_organism_attribute()
        self.__add_attributes(sample, biomaterial)
        return sample

    @staticmethod
    def __add_attributes(sample: Sample, biomaterial: dict):
        converted_attributes = JsonMapper(biomaterial).map(ATTRIBUTE_SPEC)
        for name, value in converted_attributes.items():
            sample.attributes.append(Attribute(name, value))
        BioSamplesConverter.__add_project_attribute(sample)

    @staticmethod
    def __add_project_attribute(sample):
        sample.attributes.append(
            Attribute(
                name='project',
                value='Human Cell Atlas'
            )
        )
