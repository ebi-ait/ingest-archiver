import unittest
from http import HTTPStatus
from unittest.mock import patch
from assertpy import assert_that
from biostudiesclient.exceptions import RestErrorException

import archiver_app
from archiver_app import app as _app

request_ctx = _app.test_request_context()
request_ctx.push()


class ArchiverAppTest(unittest.TestCase):
    def setUp(self):
        _app.testing = True
        self.app = _app.test_client()

    @patch('archiver_app.request')
    @patch('archiver_app.config')
    @patch('archiver.direct.direct_archiver_from_config')
    def test_when_archive_respond_with_error_then_direct_archiving_returns_the_error_message(
            self, mock_direct_archiver_from_config, mock_config, mock_request):
        # given
        request_timeout_status = HTTPStatus.REQUEST_TIMEOUT
        error_message = 'Request timed out.'
        archive_failed_message = 'Archiving failed.'
        mock_direct_archiver_from_config.side_effect = RestErrorException(error_message, request_timeout_status)
        archiver_app.direct_archiver_from_config = mock_direct_archiver_from_config
        api_key = 'API-KEY'
        mock_config.ARCHIVER_API_KEY = api_key

        mock_request.get_json.return_value = {
            'submission_uuid': '123-456-789',
            'is_direct_archiving': True
        }

        mock_headers = {
            'Api-Key': api_key
        }
        mock_request.headers = mock_headers

        # when
        response = self.app.post(
            '/archiveSubmissions',
            data=mock_request
        ).json

        # then
        assert_that(response.get('error_status_code')).is_equal_to(request_timeout_status)
        assert_that(response.get('message')).is_equal_to(archive_failed_message)
        assert_that(response.get('detailed_error_message')).is_equal_to(error_message)


if __name__ == '__main__':
    unittest.main()
