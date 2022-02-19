import unittest

from hca.submission import HcaSubmission
from tests.unit.utils import make_ingest_entity, random_id, random_uuid


class TestHcaSubmission(unittest.TestCase):
    def setUp(self) -> None:
        # Given
        self.entity_type_1 = 'projects'
        self.entity_type_2 = 'biomaterials'
        self.test_id1 = random_id()
        self.test_id2 = random_id()
        self.test_uuid1 = random_uuid()
        self.test_uuid2 = random_uuid()
        self.project_schema_type = 'project'
        self.biomaterial_schema_type = 'biomaterial'
        self.project_json = make_ingest_entity(self.entity_type_1, self.project_schema_type, self.test_id1, self.test_uuid1)
        self.biomaterial_json = \
            make_ingest_entity(self.entity_type_2, self.biomaterial_schema_type, self.test_id2, self.test_uuid2)
        self.submission = HcaSubmission()
        # When
        self.test_project = self.submission.map_ingest_entity(self.project_json)
        self.test_biomaterial = self.submission.map_ingest_entity(self.biomaterial_json)

    def test_added_entity_is_contained_in_submission(self):
        # Then
        self.assertTrue(self.submission.contains_entity(self.project_json))
        self.assertTrue(self.submission.contains_entity_by_uuid(self.entity_type_1, self.test_uuid1))
        self.assertTrue(self.submission.get_entity(self.entity_type_1, self.test_id1))

    def test_entity_attributes_are_equal_to_source(self):
        # Then
        self.assertEqual(self.project_json, self.test_project.attributes)

    def test_added_entity_is_equal_to_entity_returned_from_submission(self):
        # When
        returned_entity = self.submission.get_entity(self.entity_type_1, self.test_id1)
        # Then
        self.assertEqual(self.test_project, returned_entity)

    def test_added_entity_is_equal_to_entity_returned_from_hca_submission_by_uuid(self):
        # When
        returned_entity = self.submission.get_entity_by_uuid(self.entity_type_1, self.test_uuid1)
        # Then
        self.assertEqual(self.test_project, returned_entity)

    def test_adding_a_duplicate_entity_returns_the_original_entity(self):
        # When
        returned_entity = self.submission.map_ingest_entity(self.project_json)
        # Then
        self.assertEqual(self.test_project, returned_entity)

    def test_duplication_entity_with_differing_content_is_ignored(self):
        # Given
        ignored_uuid = random_uuid()
        duplicate_test_case = make_ingest_entity(self.entity_type_1, self.project_schema_type, self.test_id1, ignored_uuid)
        # When
        duplicate_entity = self.submission.map_ingest_entity(duplicate_test_case)
        # Then
        self.assertEqual(self.test_project, duplicate_entity)
        self.assertEqual(self.test_uuid1, self.test_project.attributes['uuid']['uuid'])
        self.assertNotEqual(ignored_uuid, self.test_project.attributes['uuid']['uuid'])

    def test_attributes_set_correctly_when_biosamples_accession_is_added_to_attributes(self):
        # When
        random_accession = random_id()
        archive_name = 'BioSamples'
        entity_type = 'biomaterials'
        self.test_project.add_accession(archive_name, random_accession)
        self.submission.add_accessions_to_attributes(self.test_project, archive_name, entity_type)
        accession_spec = self.submission.get_accession_spec_by_archive(archive_name)
        accession_mapper = accession_spec.get(entity_type)
        accession_location = accession_mapper.mapping[0].split('.')
        # Then
        accession = self.__get_accession_from_entity_attributes(self.test_project, accession_location)
        self.assertEqual(random_accession, accession)

    def test_attributes_set_correctly_when_biostudies_accession_is_added_to_attributes(self):
        # When
        random_accession = random_id()
        archive_name = 'BioStudies'
        entity_type = 'projects'
        self.test_project.add_accession(archive_name, random_accession)
        self.submission.add_accessions_to_attributes(self.test_project, archive_name, entity_type)
        accession_spec = self.submission.get_accession_spec_by_archive(archive_name)
        accession_mapper = accession_spec.get(entity_type)
        accession_location = accession_mapper.mapping[0].split('.')

        # Then
        accession = self.__get_accession_from_entity_attributes(self.test_project, accession_location)
        self.assertEqual(len(accession), 1)
        self.assertEqual(random_accession, accession[0])

    def test_attributes_set_correctly_when_ena_sample_accession_is_added_to_attributes(self):
        # When
        random_accession = random_id()
        archive_name = 'ENA'
        entity_type = 'biomaterials'
        self.test_biomaterial.add_accession(archive_name, random_accession)
        self.submission.add_accessions_to_attributes(self.test_biomaterial, archive_name, entity_type)
        accession_spec = self.submission.get_accession_spec_by_archive(archive_name)
        accession_mapper = accession_spec.get(entity_type)
        accession_location = accession_mapper.mapping[0].split('.')

        # Then
        accession = self.__get_accession_from_entity_attributes(self.test_biomaterial, accession_location)
        self.assertEqual(random_accession, accession)

    @staticmethod
    def __get_accession_from_entity_attributes(entity_under_test, accession_location):
        value = entity_under_test.attributes
        for location in accession_location:
            value = value.get(location, {})
        accession = value
        return accession


if __name__ == '__main__':
    unittest.main()
