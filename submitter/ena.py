from datetime import date
from enum import Enum
from http import HTTPStatus
from typing import Dict, Tuple

import requests
from requests import Response
from requests.auth import HTTPBasicAuth


class EnaAction(Enum):
    ADD = 'ADD'
    MODIFY = 'MODIFY'


class EnaError(Exception):
    pass


# TODO this class needs to go to the submission_broker library under the submission_broker.services package
class Ena:

    def __init__(self, ena_submission_url=None, username=None, password=None):
        self.url = ena_submission_url
        self.auth = HTTPBasicAuth(username, password)

    def send_submission(self, ena_files: Dict[str, Tuple[str, str]], action: EnaAction = None, hold_date: str = None, center_name: str = None ):
        data = {}
        if action:
            data['ACTION'] = action.value
        if hold_date:
            data['HOLD_DATE'] = hold_date
        if center_name:
            data['CENTER_NAME'] = center_name
        response: Response = requests.post(self.url, auth=self.auth, data=data, files=ena_files)
        if response.status_code == HTTPStatus(200):
            return response.content
        else:
            message = f'ENA Responded with: HTTP{response.status_code}'
            error = response.json()
            if error:
                raise EnaError(f"{message} {error['error']} {error['message']}")
            raise EnaError(message)
