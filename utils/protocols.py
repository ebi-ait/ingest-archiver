from api.ontology import OntologyAPI

ONTOLOGY_10x_PARENT = "EFO:0008995"
ONTOLOGY_10xV2_PARENT = "EFO:0009310"
ONTOLOGY_10xV3_PARENT = "EFO:0009898"


def is_10x(ontology_api: OntologyAPI, library_preparation_protocol : dict):
    library_construction = get_library_construction(library_preparation_protocol)
    return ontology_api.is_equal_or_descendant(ONTOLOGY_10x_PARENT, library_construction)


def map_10x_bam_schema(ontology_api: OntologyAPI, library_preparation_protocol: dict):
    library_construction = get_library_construction(library_preparation_protocol)
    if ontology_api.is_equal_or_descendant(ONTOLOGY_10xV2_PARENT, library_construction):
        return '10xV2'
    if ontology_api.is_equal_or_descendant(ONTOLOGY_10xV3_PARENT, library_construction):
        return '10xV3'
    return None


def get_library_construction(library_preparation_protocol: dict):
    content = library_preparation_protocol.get("content", {})
    library_construction = content.get("library_construction_approach", content.get("library_construction_method", {}))
    library_construction_ontology = library_construction.get('ontology')
    if not library_construction_ontology:
        raise ProtocolError(f'Could not determine library construction from library_preparation_protocol: {library_preparation_protocol}')
    return library_construction_ontology


class ProtocolError(Exception):
    """Class for protocol exceptions."""