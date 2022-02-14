import unittest

from assertpy import assert_that

from hca.accession_mapper import AccessionMapper
from hca.submission import HcaSubmission
from tests.unit.utils import make_ingest_entity, random_id, random_uuid


class MyTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.entity_type_1 = 'projects'
        self.test_id1 = random_id()
        self.test_uuid1 = random_uuid()
        self.project_schema_type = 'project'

        self.project_json = make_ingest_entity(self.entity_type_1, self.project_schema_type, self.test_id1,
                                               self.test_uuid1)
        self.submission = HcaSubmission()
        self.test_project = self.submission.map_ingest_entity(self.project_json)

    def test_when_passing_location_and_string_type_accession_set_correctly(self):
        accession = 'test_accession'
        accession_location = ['content.biomaterial_core.biosamples_accession']
        accession_location_list = accession_location[0].split('.')
        accession_type = 'string'
        entity = self.test_project

        AccessionMapper.set_accession_by_attribute_location(accession, accession_location, accession_type, entity)

        value = entity.attributes
        for location in accession_location_list:
            value = value.get(location, {})
        assert_that(value).is_equal_to(accession)

    def test_when_passing_location_and_array_type_accession_set_correctly(self):
        accession = 'test_accession'
        accession_location = ['content.biomaterial_core.biostudies_accession']
        accession_location_list = accession_location[0].split('.')
        accession_type = 'array'
        entity = self.test_project

        AccessionMapper.set_accession_by_attribute_location(accession, accession_location, accession_type, entity)

        value = entity.attributes
        for location in accession_location_list:
            value = value.get(location, {})
        assert_that(value).is_equal_to([accession])

    def test_when_entity_has_an_accession_it_is_being_add_by_service_name(self):
        accession = 'test_accession'
        service = 'BioStudies'
        self.test_project.attributes.setdefault('content', {})['biostudies_accessions'] = accession

        AccessionMapper.set_accessions_from_attributes(self.test_project)

        assert_that(self.test_project.get_accession(service)).is_equal_to(accession)


if __name__ == '__main__':
    unittest.main()
