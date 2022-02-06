from unittest import TestCase

from archiver.data_archiver import DataArchiver


class TestDataArchiver(TestCase):

    def test_handle_request_invalid_empty_req(self):
        response = DataArchiver().handle_request({}) # empty req
        self.assertTrue(response.message == DataArchiver.INVALID_REQUEST)

    def test_handle_request_invalid_missing_required(self):
        response = DataArchiver().handle_request({ 'uuid': ''}) # should be 'sub_uuid'
        self.assertTrue(response.message == DataArchiver.INVALID_REQUEST)

    def test_handle_request_valid_req(self):
        response = DataArchiver().handle_request({ 'sub_uuid': 'test'})
        self.assertTrue(response.message == DataArchiver.REQUEST_SUCCESSFUL)
