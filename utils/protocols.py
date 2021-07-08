import re
from api.ontology import OntologyAPI

ONTOLOGY_10x_PARENT = "EFO:0008995"
ONTOLOGY_3PRIME_PARENT = "EFO:0030003"
ONTOLOGY_5PRIME_PARENT = "EFO:0030004"

ONTOLOGY_CITESEQ = "EFO:0009294"


def is_10x(ontology_api: OntologyAPI, library_preparation_protocol: dict):
    library_construction = get_library_construction(library_preparation_protocol)
    if library_construction == ONTOLOGY_CITESEQ:
        return True
    return ontology_api.is_equal_or_descendant(ONTOLOGY_3PRIME_PARENT, library_construction) or \
           ontology_api.is_equal_or_descendant(ONTOLOGY_5PRIME_PARENT, library_construction)


def map_10x_bam_schema(ontology_api: OntologyAPI, library_preparation_protocol: dict):
    library_construction = get_library_construction(library_preparation_protocol)
    if library_construction == ONTOLOGY_CITESEQ:
        return '10xV2'
    if is_leaf_term(ontology_api, library_construction):
        return f'10x{version_10x_by_label(ontology_api, library_preparation_protocol)}'
    return None


def is_leaf_term(ontology_api: OntologyAPI, library_construction: str):
    term = ontology_api.search(library_construction)
    ontology = term['ontology_name']
    iri = term['iri']
    return False if ontology_api.get_descendants(ontology, iri) else True


def version_10x_by_label(ontology_api: OntologyAPI, library_preparation_protocol: dict):
    library_construction = get_library_construction(library_preparation_protocol)
    term = ontology_api.search(library_construction)
    label = term['label']
    version = re.findall('v[23]$|$', label)[0]
    if not version:
        raise ProtocolError(f'Could not determine version from {label}')
    return version.capitalize()


def get_library_construction(library_preparation_protocol: dict):
    content = library_preparation_protocol.get("content", {})
    library_construction = content.get("library_construction_approach", content.get("library_construction_method", {}))
    library_construction_ontology = library_construction.get('ontology')
    if not library_construction_ontology:
        raise ProtocolError(
            f'Could not determine library construction from library_preparation_protocol: {library_preparation_protocol}')
    return library_construction_ontology


class ProtocolError(Exception):
    """Class for protocol exceptions."""
