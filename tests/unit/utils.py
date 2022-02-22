import string
import random
import uuid


def make_ingest_entity(ingest_type: str,
                       schema_type: str,
                       ingest_index: str,
                       ingest_uuid: str = None,
                       attributes: dict = None,
                       extra_links=None
                       ) -> dict:
    if not attributes:
        attributes = {
            'releaseDate': '2020-01-01T11:22:33Z',
            'schema_type': schema_type
        }
    if ingest_uuid:
        attributes['uuid'] = {'uuid': ingest_uuid}
    entity_uri = f'https://test_case.org/{ingest_type}/{ingest_index}'
    links = {
            'self': {
                'href': entity_uri
            }
        }
    if extra_links:
        for link_name, link_suffix in extra_links:
            links[link_name] = {
                    'href': f'{entity_uri}/{link_suffix}'
                }
    attributes['_links'] = links
    return attributes


def random_id(length: int = None):
    if not length:
        length = 24
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


def random_uuid():
    return uuid.uuid4().__str__()
