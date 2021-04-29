import unittest

from hca.submission import HcaSubmission
from tests.hca.utils import make_ingest_entity, random_id, random_uuid


class TestHcaSubmission(unittest.TestCase):
    def test_added_entity_is_contained_in_hca_submission(self):
        # Given
        test_type = 'hca_submission_test'
        test_uuid = random_uuid()
        test_case = make_ingest_entity(test_type, random_id(), test_uuid)
        submission = HcaSubmission()

        # When
        submission.map_ingest_entity(test_case)

        # Then
        self.assertTrue(submission.contains_entity(test_case))
        self.assertTrue(submission.contains_entity_by_uuid(test_type, test_uuid))

    def test_added_entity_is_contained_in_submission(self):
        # Given
        test_type = 'submission_test'
        test_id = random_id()
        test_case = make_ingest_entity(test_type, test_id, random_uuid())
        submission = HcaSubmission()

        # When
        submission.map_ingest_entity(test_case)

        # Then
        self.assertTrue(submission.get_entity(test_type, test_id))

    def test_entity_attributes_are_equal_to_source(self):
        # Given
        test_type = 'attribute_equality_test'
        test_case = make_ingest_entity(test_type, random_id(), random_uuid())
        submission = HcaSubmission()

        # When
        test_entity = submission.map_ingest_entity(test_case)

        # Then
        self.assertEqual(test_case, test_entity.attributes)

    def test_added_entity_is_equal_to_entity_returned_from_submission(self):
        # Given
        test_type = 'entity_equality_test'
        test_id = random_id()
        test_case = make_ingest_entity(test_type, test_id, random_uuid())
        submission = HcaSubmission()

        # When
        added_entity = submission.map_ingest_entity(test_case)

        # Then
        self.assertEqual(added_entity, submission.get_entity(test_type, test_id))

    def test_added_entity_is_equal_to_entity_returned_from_hca_submission_by_uuid(self):
        # Given
        ingest_type = 'uuid_test'
        test_uuid = random_uuid()
        test_case = make_ingest_entity(ingest_type, random_id(), test_uuid)
        submission = HcaSubmission()

        # When
        added_entity = submission.map_ingest_entity(test_case)

        # Then
        self.assertEqual(added_entity, submission.get_entity_by_uuid(ingest_type, test_uuid))

    def test_duplicate_entities_with_matching_ids_are_equal(self):
        # Given
        ingest_type = 'duplicate_test'
        test_id = random_id()
        test_case_1 = make_ingest_entity(ingest_type, test_id, random_uuid())
        test_case_2 = make_ingest_entity(ingest_type, test_id, random_uuid())
        submission = HcaSubmission()

        # When
        entity_1 = submission.map_ingest_entity(test_case_1)
        entity_2 = submission.map_ingest_entity(test_case_2)

        # Then
        self.assertEqual(entity_1, entity_2)


if __name__ == '__main__':
    unittest.main()
