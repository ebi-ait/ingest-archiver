from collections import Mapping

from conversion.data_node import DataNode

KEYWORD_MARKER = '$'

SPEC_ANCHOR = '$on'
SPEC_FILTER = '$filter'


class JsonMapper:

    def __init__(self, source: dict):
        self.root_node = DataNode(source)

    def map(self, using={}, on=''):
        spec = using
        self._check_if_readable(spec)
        anchor = self._determine_anchor(on, spec)
        node = self.root_node if not anchor else self._anchor_node(anchor)
        if isinstance(node, list):
            result = []
            for item in node:
                mapping = self._apply_node_spec(item, anchor, spec)
                if len(mapping) > 0:
                    result.append(mapping)
        else:
            result = self._apply_node_spec(node, anchor, spec)
        return result

    @staticmethod
    def _check_if_readable(spec):
        if not (isinstance(spec, list) or isinstance(spec, dict)):
            raise UnreadableSpecification

    @staticmethod
    def _determine_anchor(field, spec):
        anchor = field
        if SPEC_ANCHOR in spec:
            anchor = f'{anchor}.{spec[SPEC_ANCHOR]}' if anchor else spec[SPEC_ANCHOR]
            del spec[SPEC_ANCHOR]
        return anchor

    def _anchor_node(self, field):
        if field:
            anchored_node = self.root_node.get(field)
            # check if anchored_node is dict-like
            if isinstance(anchored_node, Mapping):
                return DataNode(anchored_node)
            # or if anchored_node is actually a list
            elif isinstance(anchored_node, list):
                return [DataNode(node) for node in anchored_node]
            else:
                raise InvalidNode(field)

    def _apply_node_spec(self, node: DataNode, anchor: str, spec: dict):
        filter_spec = spec.get(SPEC_FILTER)
        if not self._passes(filter_spec, node):
            return {}
        result = DataNode()
        for field_name, field_spec in spec.items():
            # skip reserved field
            if not field_name.startswith(KEYWORD_MARKER):
                self._check_if_readable(field_spec)
                field_value = None
                if isinstance(field_spec, list):
                    field_value = self._apply_field_spec(node, field_spec)
                elif isinstance(field_spec, dict):
                    field_value = self.map(using=field_spec, on=anchor)
                if field_value is not None:
                    result[field_name] = field_value
        return result.as_dict()

    @staticmethod
    def _passes(filter_spec: list, node: DataNode):
        if filter_spec is None:
            return True
        filter_field = filter_spec[0]
        value = node.get(filter_field)
        passing = True
        if value is not None:
            filter_args = [value]
            filter_args.extend(filter_spec[2:])
            do_filter = filter_spec[1]
            passing = bool(do_filter(*filter_args))
        return passing

    @staticmethod
    def _apply_field_spec(node: DataNode, spec: list):
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


class UnreadableSpecification(Exception):

    def __init__(self):
        super(UnreadableSpecification, self).__init__('Provided specification of unreadable type.')
