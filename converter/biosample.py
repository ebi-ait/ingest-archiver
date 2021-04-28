from biosamples_v4.models import Sample, Attribute

ATTRIBUTE_NAMES = {
    'content.biomaterial_core.biomaterial_id': 'Biomaterial Core - Biomaterial Id',
    'content.describedBy': 'HCA Biomaterial Type',
    'uuid.uuid': 'HCA Biomaterial UUID',
    'content.is_living': 'Is Living',
    'content.medical_history.smoking_history': 'Medical History - Smoking History',
    'content.sex': 'Sex',
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
        for key, attribute_name in ATTRIBUTE_NAMES.items():
            indexes = str(key).split('.')
            indexes.reverse()
            value = BioSamplesConverter.__get_attr_value(biomaterial_attributes, indexes)
            sample.attributes.append(
                Attribute(
                    name=attribute_name,
                    value=value
                )
            )
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
    def __get_attr_value(biomaterial_attributes, indexes: list) -> str:
        index = indexes.pop()
        biomaterial_attribute = biomaterial_attributes[index]

        if index == 'describedBy':
            biomaterial_attribute = str(biomaterial_attribute).split('/')[-1]

        if len(indexes) > 0:
            biomaterial_attribute = BioSamplesConverter.__get_attr_value(biomaterial_attribute, indexes)

        return biomaterial_attribute

    @staticmethod
    def __named_attribute(biomaterial: dict, attribute_name: str, default=None):
        return biomaterial[attribute_name] if attribute_name in biomaterial else default
