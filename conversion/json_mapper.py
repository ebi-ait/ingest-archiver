class NodeMapping:

    def using(self, mapping_spec: dict):
        return {}


class JsonMapper:

    def __init__(self, source):
        pass

    def map(self, field_key='') -> NodeMapping:
        return NodeMapping()
