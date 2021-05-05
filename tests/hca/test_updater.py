import unittest
from mock import MagicMock, call

from hca.submission import HcaSubmission
from hca.updater import HcaUpdater
from tests.utils import random_id, random_uuid, make_ingest_entity


class TestHcaUpdater(unittest.TestCase):
    def setUp(self) -> None:
        self.ingest = MagicMock()
        self.ingest.patch = MagicMock()
        self.updater = HcaUpdater(self.ingest)
        self.submission = HcaSubmission()

    def test_update_submission_calls_patch_once_per_entity(self):
        # Given
        self.map_random_entities(self.submission, 5)
        calls = []
        call_count = 0
        for entities in self.submission.get_all_entities().values():
            for entity in entities:
                call_count += 1
                calls.append(call(HcaSubmission.get_link(entity.attributes, 'self'), entity.attributes))

        # When
        self.updater.update_submission(self.submission)

        # Then
        self.ingest.patch.assert_has_calls(calls, any_order=True)
        self.assertEqual(call_count, self.ingest.patch.call_count)

    def test_update_entity_type_calls_patch_once_per_matching_entity_type(self):
        # Given
        test_type = random_id()
        self.map_random_entities(self.submission, 5, test_type)
        self.map_random_entities(self.submission, 5)
        calls = []
        call_count = 0
        for entity in self.submission.get_entities(test_type):
            call_count += 1
            calls.append(call(HcaSubmission.get_link(entity.attributes, 'self'), entity.attributes))

        # When
        self.updater.update_entity_type(self.submission, test_type)

        # Then
        self.ingest.patch.assert_has_calls(calls, any_order=True)
        self.assertEqual(call_count, self.ingest.patch.call_count)

    def test_update_entities_only_patches_passed_entities(self):
        # Given
        updated_entities = self.map_random_entities(self.submission, 5)
        self.map_random_entities(self.submission, 5)
        calls = []
        call_count = 0
        for entity in updated_entities:
            call_count += 1
            calls.append(call(HcaSubmission.get_link(entity.attributes, 'self'), entity.attributes))

        # When
        self.updater.update_entities(updated_entities)

        # Then
        self.ingest.patch.assert_has_calls(calls, any_order=True)
        self.assertEqual(call_count, self.ingest.patch.call_count)

    def test_update_entity_only_patches_entity(self):
        # Given
        test_case = self.map_random_entities(self.submission, 5).pop()
        self_link = HcaSubmission.get_link(test_case.attributes, 'self')

        # When
        self.updater.update_entity(test_case)

        # Then
        self.ingest.patch.assert_called_once_with(self_link, test_case.attributes)

    @staticmethod
    def map_random_entities(
            submission: HcaSubmission,
            entity_count: int,
            entity_type: str = None
    ):
        entity_list = []
        for i in range(0, entity_count):
            entity_list.append(
                submission.map_ingest_entity(
                    make_ingest_entity(
                        entity_type if entity_type else random_id(),
                        random_id(),
                        random_uuid()
                    )
                )
            )
        return entity_list


if __name__ == '__main__':
    unittest.main()
