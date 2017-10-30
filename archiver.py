import json
from flatten_json import flatten

HCA_USI_KEY_MAP = {
    "uuid_uuid": "alias",
    "content_id": "title",
    "content_species_ontology": "taxonId",
    "content_species_text": "taxon"
}


def extract_fields(hca_data):
    flattened_hca_data = flatten(hca_data)

    extracted_data = {"attributes": extract_attributes(flattened_hca_data)}

    for key, new_key in HCA_USI_KEY_MAP.items():
        if key in flattened_hca_data:
            extracted_data[new_key] = flattened_hca_data[key]

    return extracted_data


def convert_to_usi(filename):
    with open(filename, encoding='utf-8') as data_file:
        hca_data = json.loads(data_file.read())

    extracted_data = extract_fields(hca_data)

    return build_output(extracted_data)


def build_output(extracted_data):
    usi_data = {"alias": extracted_data["alias"],
                "team": {
                    "name": 'self.hca-user'
                },
                'title': extracted_data["title"],
                "description": "",
                "attributes": extracted_data["attributes"],
                "sampleRelationships": [],
                "taxonId": extracted_data["taxonId"],
                "taxon": extracted_data["taxon"]
                }
    return usi_data


def extract_attributes(flattened_hca_data):
    attributes = []
    prefix = "content_"
    for key, value in flattened_hca_data.items():
        if key.startswith(prefix) and key not in HCA_USI_KEY_MAP:
            attr = {
                "name": key.replace(prefix, ""),
                "value": value,
                "terms": []
            }
            attributes.append(attr)

    attributes.append({
        "name": "release",
        "value": flattened_hca_data["submissionDate"],
        "terms": []
    })
    return attributes
