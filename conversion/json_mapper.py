from collections import Mapping

from conversion.data_node import DataNode


class JsonMapper:

    def __init__(self, source: dict):
        self.root_node = DataNode(source)

    def map(self, on='', using={}):
        node = self.root_node if not on else self._anchor_node(on)
        spec = using
        result = DataNode()
        for field_name, spec in spec.items():
            if isinstance(spec, list):
                field_value = self._do_map(node, spec)
            elif isinstance(spec, dict):
                field_value = JsonMapper(node).map(using=spec)
            if field_value:
                result[field_name] = field_value
        return result.as_dict()

    def _anchor_node(self, field):
        if field:
            anchored_node = self.root_node.get(field)
            # check if anchored_node is dict-like
            if isinstance(anchored_node, Mapping):
                return DataNode(anchored_node)
            else:
                raise InvalidNode(field)

    @staticmethod
    def _do_map(node, spec):
        source_field_name = spec[0]
        field_value = node.get(source_field_name)
        has_customisation = len(spec) > 1
        if has_customisation:
            operation = spec[1]
            args = [field_value]
            args.extend(spec[2:])
            field_value = operation(*args)
        return field_value


class InvalidNode(Exception):

    def __init__(self, field):
        super(InvalidNode, self).__init__(f'Invalid node [{field}].')
        self.field = field
