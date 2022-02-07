from unittest import TestCase
from unittest.mock import Mock

from archiver.data_archiver import DataArchiver


class TestDataArchiver(TestCase):

    def setUp(self):
        self.mock = Mock()
        self.data_archiver = DataArchiver(self.mock)

    def test_handle_request_invalid_empty_req(self):
        response = self.data_archiver.send_request({}) # empty req
        self.assertTrue(response['message'] == DataArchiver.INVALID_REQUEST)

    def test_handle_request_invalid_missing_required(self):
        response = self.data_archiver.send_request({ 'uuid': ''}) # should be 'sub_uuid'
        self.assertTrue(response['message'] == DataArchiver.INVALID_REQUEST)

    def test_handle_request_valid_req(self):
        response = self.data_archiver.send_request({ 'sub_uuid': 'test'})
        self.mock.send.assert_called_once()
        self.assertTrue(response['message'] == DataArchiver.REQUEST_SUCCESSFUL)
