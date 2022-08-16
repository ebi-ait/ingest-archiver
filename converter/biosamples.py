from datetime import datetime

from biosamples_v4.models import Sample, Attribute
from json_converter.json_mapper import JsonMapper

from . import get_concrete_type
from .errors import MissingBioSamplesDomain

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

    def convert(self, biomaterial: dict, additional_attributes: dict = None) -> Sample:
        domain = additional_attributes.get('domain')
        release_date = additional_attributes.get('release_date')
        existing_accession = additional_attributes.get('accession')

        if not domain and not self.default_domain:
            raise MissingBioSamplesDomain()
        biomaterial_content = biomaterial.get('content', {})
        biomaterial_core = biomaterial_content.get('biomaterial_core', {})
        sample_accession = self.__define_accession(existing_accession, biomaterial_core)
        biomaterial_name = biomaterial_core.get('biomaterial_name') if biomaterial_core.get('biomaterial_name') \
            else biomaterial_core.get('biomaterial_id', '')
        sample = Sample(
            accession=sample_accession,
            name=biomaterial_name,
            domain=domain if domain else self.default_domain,
            species=biomaterial_content['genus_species'][0].get('ontology_label') if biomaterial_content.get(
                'genus_species') else None,
            ncbi_taxon_id=biomaterial_core.get('ncbi_taxon_id')[0] if biomaterial_core.get('ncbi_taxon_id') else None,
            update=self.__convert_datetime(biomaterial.get('updateDate')),
            release=self.__convert_datetime(release_date if release_date else biomaterial.get('submissionDate'))
        )
        sample._append_organism_attribute()
        self.__add_attributes(sample, biomaterial)
        return sample

    @staticmethod
    def __define_accession(existing_accession: str, biomaterial_core):
        accession = existing_accession if existing_accession and len(existing_accession) > 0 \
            else biomaterial_core.get('biosamples_accession')

        if accession and len(accession) > 0:
            return accession
        else:
            return None

    @staticmethod
    def __add_attributes(sample: Sample, biomaterial: dict):
        converted_attributes = JsonMapper(biomaterial).map(ATTRIBUTE_SPEC)
        for name, value in converted_attributes.items():
            sample.attributes.append(Attribute(name, value))
        BioSamplesConverter.__add_external_references(sample, biomaterial)
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
    def __add_external_references(sample: Sample, biomaterial: dict):
        if 'externalReferences' in biomaterial:
            sample.external_references.extend(biomaterial.get('externalReferences'))

    @staticmethod
    def __convert_datetime(datetime_str: str) -> datetime:
        if datetime_str:
            if '.' in datetime_str:
                datetime_format = '%Y-%m-%dT%H:%M:%S.%fZ'
            else:
                datetime_format = '%Y-%m-%dT%H:%M:%SZ'
            return datetime.strptime(datetime_str, datetime_format)
