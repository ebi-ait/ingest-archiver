from collections import Mapping

from conversion.data_node import DataNode


class NodeMapping:

    def __init__(self, node: DataNode, anchor: str):
        if anchor:
            anchored_node = node.get(anchor)
            # check if anchored_node is dict-like
            if isinstance(anchored_node, Mapping):
                self.node = DataNode(anchored_node)
            else:
                raise InvalidNode(anchor)
        else:
            self.node = node

    def using(self, mapping_spec: dict) -> dict:
        result = {}
        for field_name, spec in mapping_spec.items():
            source_field_name = spec[0]
            field_value = self.node.get(source_field_name)
            has_customisation = len(spec) > 0
            if has_customisation:
                operation = spec[1]
                args = [field_value]
                args.extend(spec[2:])
                field_value = operation(*args)
            result[field_name] = field_value
        return result


class JsonMapper:

    def __init__(self, source: dict):
        self.root_node = DataNode(source)

    def map(self, field_key='') -> NodeMapping:
        return NodeMapping(self.root_node, field_key)


class InvalidNode(Exception):

    def __init__(self, field):
        super(InvalidNode, self).__init__(f'Invalid node [{field}].')
        self.field = field
