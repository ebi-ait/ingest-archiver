from conversion.data_node import DataNode


class NodeMapping:

    def __init__(self, node: DataNode):
        self.node = node

    def using(self, mapping_spec: dict):
        result = {}
        for field_name, spec in mapping_spec.items():
            source_field_name = spec[0]
            result[field_name] = self.node.get(source_field_name)
        return result


class JsonMapper:

    def __init__(self, source: dict):
        self.root_node = DataNode(source)

    def map(self, field_key='') -> NodeMapping:
        return NodeMapping(self.root_node)
