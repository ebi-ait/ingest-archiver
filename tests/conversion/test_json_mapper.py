import json
from unittest import TestCase

from conversion.json_mapper import JsonMapper, InvalidNode, UnreadableSpecification


class JsonMapperTest(TestCase):

    def test_map_object(self):
        # given:
        json_object = json.loads('''{
            "user_name": "jdelacruz",
            "user_age": 31
        }''')

        # when:
        converted_json = JsonMapper(json_object).map({
            'name': ['user_name'],
            'age': ['user_age']
        })

        # then:
        self.assertIsNotNone(converted_json)
        self.assertEqual('jdelacruz', converted_json['name'])
        self.assertEqual(31, converted_json['age'])

    def test_map_object_using_field_chaining(self):
        # given:
        json_object = json.loads('''{
            "name": "John Doe",
            "address": {
                "city": "London",
                "country": "UK"
            }
        }''')

        # when:
        profile_json = JsonMapper(json_object).map({
            'user.profile': ['name'],
            'user.address_city': ['address.city'],
            'user.address_country': ['address.country']
        })

        # then:
        self.assertIsNotNone(profile_json)
        self.assertEqual('John Doe', profile_json.get('user', {}).get('profile'))
        self.assertEqual('London', profile_json.get('user', {}).get('address_city'))
        self.assertEqual('UK', profile_json.get('user', {}).get('address_country'))

    def test_map_object_with_anchored_key(self):
        # given:
        json_object = json.loads('''{
            "user": {
                "name": "Jane Doe"
            },
            "address": {
                "city": "Cambridge",
                "country": "UK"
            }
        }''')

        # when:
        address_json = JsonMapper(json_object).map(
            on='address',
            using={
                'address_city': ['city'],
                'address_country': ['country']
            })

        # then:
        self.assertIsNotNone(address_json)
        self.assertEqual('Cambridge', address_json['address_city'])
        self.assertEqual('UK', address_json['address_country'])

    def test_map_object_using_spec_based_anchor(self):
        # given:
        json_object = json.loads('''{
            "shipping_info": {
                "recipient": "Kamado Tanjiro",
                "address": "Tokyo, Japan"
            }
        }''')

        # when:
        delivery_json = JsonMapper(json_object).map({
            '$on': 'shipping_info',
            'name': ['recipient'],
            'location': ['address']
        })

        # then:
        self.assertEqual('Kamado Tanjiro', delivery_json.get('name'))
        self.assertEqual('Tokyo, Japan', delivery_json.get('location'))

    def test_map_object_using_chained_spec_based_anchors(self):
        # given:
        json_object = json.loads('''{
            "user": {
                "profile": {
                    "name": "Kamado Nezuko",
                    "location": "hako no naka"
                }
            }
        }''')

        # when:
        person_json = JsonMapper(json_object).map({
            '$on': 'user',
            'person': {
                '$on': 'profile',
                'known_by': ['name']
            }
        })

        # then:
        self.assertEqual('Kamado Nezuko', person_json.get('person', {}).get('known_by'))

    def test_map_object_with_non_node_anchor(self):
        # given:
        json_object = json.loads('''{
            "name": "Boaty McBoatface"
        }''')
        mapper = JsonMapper(json_object)

        # expect:
        with self.assertRaises(InvalidNode):
            mapper.map(on='name')

        # and: raise exception if anchor can't be found
        with self.assertRaises(InvalidNode):
            mapper.map(on='non.existent.node')

    def test_map_object_with_custom_processing(self):
        # given:
        json_object = json.loads('''{
            "name": "Pedro,Catapang,de Guzman",
            "age": 44
        }''')

        # and:
        def parse_name(*args):
            name = args[0]
            index = args[1]
            return name.split(',')[index]

        # and:
        def fake_age(*args):
            age = args[0]
            return age - 10

        # when:
        resulting_json = JsonMapper(json_object).map({
            'first_name': ['name', parse_name, 0],
            'middle_name': ['name', parse_name, 1],
            'last_name': ['name', parse_name, 2],
            'fake_age': ['age', fake_age]
        })

        # then:
        self.assertEqual('Pedro', resulting_json['first_name'])
        self.assertEqual('Catapang', resulting_json['middle_name'])
        self.assertEqual('de Guzman', resulting_json['last_name'])
        self.assertEqual(34, resulting_json['fake_age'])

    def test_map_object_with_nested_spec(self):
        # given:
        json_object = json.loads('''{
            "first_name": "Vanessa",
            "last_name": "Doofenshmirtz"
        }''')

        # when:
        profile_json = JsonMapper(json_object).map({
            'profile': {
                'first_name': ['first_name'],
                'last_name': ['last_name']
            }
        })

        # then:
        profile = profile_json.get('profile')
        self.assertIsNotNone(profile)
        self.assertEqual('Vanessa', profile.get('first_name'))
        self.assertEqual('Doofenshmirtz', profile.get('last_name'))

    def test_map_list_of_objects(self):
        # given:
        json_object = json.loads('''{
            "contacts": [
                {
                    "name": "James",
                    "phone": "55556161"
                },
                {
                    "name": "Ana",
                    "phone": "55510103"
                }
            ]
        }''')

        # when:
        people = JsonMapper(json_object).map(on='contacts', using={
            'known_by': ['name']
        })

        # then:
        self.assertEqual(2, len(people))
        names = [person.get('known_by') for person in people]
        self.assertTrue('Ana' in names)
        self.assertTrue('James' in names)

    def test_map_list_of_objects_with_nested_anchoring(self):
        # given:
        json_object = json.loads('''{
            "social_network": {
                "friends": [
                    {
                        "name": "Carl",
                        "age": 24
                    },
                    {
                        "name": "Tina",
                        "age": 22
                    },
                    {
                        "name": "Oscar",
                        "age": 22
                    }
                ]
            }
        }''')

        # when:
        people_json = JsonMapper(json_object).map({
            '$on': 'social_network',
            'people': {
                '$on': 'friends',
                'person_name': ['name'],
                'person_age': ['age']
            }
        })

        # then:
        people = people_json.get('people')
        self.assertIsNotNone(people)
        self.assertEqual(3, len(people))

    # TODO consider required field mode
    def test_map_object_ignore_missing_fields(self):
        # given:
        json_object = json.loads('''{
            "first_name": "Juan",
            "last_name": "dela Cruz"
        }''')

        # when:
        person_json = JsonMapper(json_object).map({
            'fname': ['first_name'],
            'mname': ['middle_name'],
            'lname': ['last_name']
        })

        # then:
        self.assertEqual('Juan', person_json.get('fname'))
        self.assertEqual('dela Cruz', person_json.get('lname'))
        self.assertTrue('mname' not in person_json)

    def test_map_object_with_invalid_spec(self):
        # given:
        json_object = json.loads('''{
            "description": "this is a test"
        }''')

        # expect: main spec
        with self.assertRaises(UnreadableSpecification) as exception:
            JsonMapper(json_object).map('spec')

        # and: field spec
        with self.assertRaises(UnreadableSpecification) as exception:
            JsonMapper(json_object).map({
                'd': 'specification'
            })
