from biosamples_v4.models import Sample, Attribute
from json_converter.json_mapper import JsonMapper


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
    def __init__(self, domain=None):
        self.domain = domain

    def convert(self, biomaterial: dict, domain:str, release_date: str = None) -> Sample:
        biomaterial_content = biomaterial['attributes']['content']
        sample = Sample(
            accession=self.__named_attribute(biomaterial_content['biomaterial_core'], 'biosamples_accession'),
            name=self.__named_attribute(biomaterial_content['biomaterial_core'], 'biomaterial_name'),
            update=self.__named_attribute(biomaterial['attributes'], 'updateDate'),
            domain=domain,
            species=self.__named_attribute(biomaterial_content['genus_species'][0], 'ontology_label'),
            ncbi_taxon_id=self.__named_attribute(biomaterial_content['biomaterial_core'], 'ncbi_taxon_id')[0]
        )
        self.__add_release_date(sample, biomaterial['attributes']['submissionDate'], release_date)
        sample._append_organism_attribute()

        self.__add_attributes(sample, biomaterial['attributes'])

        return sample

    @staticmethod
    def __add_release_date(sample, submission_date, release_date):
        if release_date:
            sample.release = release_date
        else:
            sample.release = submission_date

    @staticmethod
    def __add_attributes(sample, biomaterial_attributes):
        converted_attributes = JsonMapper(biomaterial_attributes).map(ATTRIBUTE_SPEC)
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

    @staticmethod
    def __named_attribute(biomaterial: dict, attribute_name: str, default=None):
        return biomaterial[attribute_name] if attribute_name in biomaterial else default
