from api import ontology


def dsp_attribute(*args):
    value = args[0]
    if value is not None:
        return [{'value': value}]


def dsp_ontology(*args):
    hca_ontology = args[0]
    if hca_ontology:
        if 'ontology_label' in hca_ontology and 'ontology' in hca_ontology:
            label: str = hca_ontology['ontology_label']
            obo_id: str = hca_ontology['ontology']
            iri = ontology.__api__.iri_from_obo_id(obo_id)
            if iri:
                return [{
                    'value': label,
                    'terms': [{'url': iri}]
                }]
        if 'text' in hca_ontology:
            return dsp_attribute(hca_ontology['text'])


def fixed_dsp_attribute(*args):
    value = args[1]
    return dsp_attribute(value)


def taxon_id(*args):
    taxon_ids = args[0]
    return taxon_ids[0] if taxon_ids and len(taxon_ids) > 0 else None


def taxon_id_attribute(*args):
    attribute_id = taxon_id(*args)
    return dsp_attribute(attribute_id)
