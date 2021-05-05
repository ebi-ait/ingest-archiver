import unittest

from hca.submission import HcaSubmission
from tests.utils import make_ingest_entity, random_id, random_uuid


class TestHcaSubmission(unittest.TestCase):
    def setUp(self) -> None:
        # Given
        self.test_type = random_id()
        self.test_id = random_id()
        self.test_uuid = random_uuid()
        self.test_case = make_ingest_entity(self.test_type, self.test_id, self.test_uuid)
        self.submission = HcaSubmission()
        # When
        self.test_entity = self.submission.map_ingest_entity(self.test_case)

    def test_added_entity_is_contained_in_submission(self):
        # Then
        self.assertTrue(self.submission.contains_entity(self.test_case))
        self.assertTrue(self.submission.contains_entity_by_uuid(self.test_type, self.test_uuid))
        self.assertTrue(self.submission.get_entity(self.test_type, self.test_id))

    def test_entity_attributes_are_equal_to_source(self):
        # Then
        self.assertEqual(self.test_case, self.test_entity.attributes)

    def test_added_entity_is_equal_to_entity_returned_from_submission(self):
        # When
        returned_entity = self.submission.get_entity(self.test_type, self.test_id)
        # Then
        self.assertEqual(self.test_entity, returned_entity)

    def test_added_entity_is_equal_to_entity_returned_from_hca_submission_by_uuid(self):
        # When
        returned_entity = self.submission.get_entity_by_uuid(self.test_type, self.test_uuid)
        # Then
        self.assertEqual(self.test_entity, returned_entity)

    def test_adding_a_duplicate_entity_returns_the_original_entity(self):
        # When
        returned_entity = self.submission.map_ingest_entity(self.test_case)
        # Then
        self.assertEqual(self.test_entity, returned_entity)

    def test_duplication_entity_with_differing_content_is_ignored(self):
        # Given
        ignored_uuid = random_uuid()
        duplicate_test_case = make_ingest_entity(self.test_type, self.test_id, ignored_uuid)
        # When
        duplicate_entity = self.submission.map_ingest_entity(duplicate_test_case)
        # Then
        self.assertEqual(self.test_entity, duplicate_entity)
        self.assertEqual(self.test_uuid, self.test_entity.attributes['uuid']['uuid'])
        self.assertNotEqual(ignored_uuid, self.test_entity.attributes['uuid']['uuid'])

    def test_attributes_set_correctly_when_biosamples_accession_is_added_to_attributes(self):
        # When
        random_accession = random_id()
        self.test_entity.add_accession('BioSamples', random_accession)
        self.submission.add_accessions_to_attributes(self.test_entity)

        # Then
        acc = self.test_entity.attributes['content']['biomaterial_core']['biosamples_accession']
        self.assertEqual(random_accession, acc)


if __name__ == '__main__':
    unittest.main()
