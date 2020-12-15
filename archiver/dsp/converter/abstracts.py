from abc import abstractmethod

from api.ontology import OntologyAPI
from archiver.base import BaseConverter
from conversion.json_mapper import JsonMapper


class BaseDspConverter(BaseConverter):
    @abstractmethod
    def convert(self, hca_data):
        pass

    @staticmethod
    def map(hca_data: dict, spec):
        return JsonMapper(hca_data).map(spec)

    @staticmethod
    def dsp_attribute(*args):
        value = args[0]
        if value is not None:
            return [{'value': value}]

    @staticmethod
    def fixed_dsp_attribute(*args):
        value = args[1]
        return BaseDspConverter.dsp_attribute(value)

    @staticmethod
    def taxon_id(*args):
        taxon_ids = args[0]
        return taxon_ids[0] if taxon_ids and len(taxon_ids) > 0 else None

    @staticmethod
    def taxon_id_attribute(*args):
        attribute_id = BaseDspConverter.taxon_id(*args)
        return BaseDspConverter.dsp_attribute(attribute_id)


class DspOntologyConverter(BaseDspConverter):
    def __init__(self, ontology_api: OntologyAPI):
        self.ontology_api = ontology_api

    @abstractmethod
    def convert(self, hca_data):
        pass

    def dsp_ontology(self, *args):
        hca_ontology = args[0]
        if hca_ontology:
            if 'ontology_label' in hca_ontology and 'ontology' in hca_ontology:
                label: str = hca_ontology['ontology_label']
                obo_id: str = hca_ontology['ontology']
                iri = self.ontology_api.iri_from_obo_id(obo_id)
                if iri:
                    return [{
                        'value': label,
                        'terms': [{'url': iri}]
                    }]
            if 'text' in hca_ontology:
                return self.dsp_attribute(hca_ontology['text'])
