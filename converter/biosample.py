from biosamples_v4.models import Sample


class BioSamplesConverter:
    def __init__(self, domain=None):
        self.domain = domain

    def convert(self, biomaterial: dict, release_date: str = None) -> Sample:
        biomaterial_content = biomaterial['attributes']['content']
        sample = Sample(
            accession=self.__named_attribute(biomaterial_content['biomaterial_core'], 'biosamples_accession'),
            name=self.__named_attribute(biomaterial_content['biomaterial_core'], 'biomaterial_name'),
            update=self.__named_attribute(biomaterial['attributes'], 'updateDate'),
            species=self.__named_attribute(biomaterial_content['genus_species'][0], 'ontology_label'),
            ncbi_taxon_id=self.__named_attribute(biomaterial_content['biomaterial_core'], 'ncbi_taxon_id')[0]
        )
        self.__add_release_date(sample, biomaterial['attributes']['submissionDate'], release_date)
        sample._append_organism_attribute()

        return sample

    @staticmethod
    def __add_release_date(sample, submission_date, release_date):
        if release_date:
            sample.release = release_date
        else:
            sample.release = submission_date

    @staticmethod
    def __named_attribute(biomaterial: dict, attribute_name: str, default=None):
        return biomaterial[attribute_name] if attribute_name in biomaterial else default
