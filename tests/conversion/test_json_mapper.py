import json
from unittest import TestCase

from conversion.json_mapper import JsonMapper


class JsonMapperTest(TestCase):

    def test_map_object(self):
        # given:
        json_object = json.dumps('{}')

        # when:
        converted_json = JsonMapper(json_object).map().using({
            'name': ['user_name'],
            'age': ['user_age']
        })

        # then:
        self.assertIsNotNone(converted_json)
