from api.ontology import OntologyAPI

ONTOLOGY_10x_PARENT = "EFO:0008995"
ONTOLOGY_10xV2_PARENT = "EFO:0009310"
ONTOLOGY_10xV3_PARENT = "EFO:0009898"


def is_10x(ontology_api: OntologyAPI, library_preparation_protocol : dict):
    library_const_approach = get_library_const_approach(library_preparation_protocol)
    if library_const_approach:
        if ONTOLOGY_10x_PARENT == library_const_approach:
            return True
        if ontology_api.is_child_of(ONTOLOGY_10x_PARENT, library_const_approach):
            return True
    return False


def map_10x_bam_schema(ontology_api: OntologyAPI, library_preparation_protocol: dict):
    library_const_approach = get_library_const_approach(library_preparation_protocol)
    if ONTOLOGY_10xV2_PARENT == library_const_approach:
        return '10xV2'
    if ontology_api.is_child_of(ONTOLOGY_10xV2_PARENT, library_const_approach):
        return '10xV2'
    if ONTOLOGY_10xV3_PARENT == library_const_approach:
        return '10xV3'
    if ontology_api.is_child_of(ONTOLOGY_10xV3_PARENT, library_const_approach):
        return '10xV3'
    return None


def get_library_const_approach(library_preparation_protocol: dict):
    content = library_preparation_protocol.get("content", {})
    library_const_approach_obj = content.get("library_construction_approach",
                                             content.get("library_construction_method", {}))
    return library_const_approach_obj.get('ontology')