import requests

import config


class AAPTokenClient:
    def __init__(self, url=None, username=None, password=None):
        self.url = url if url else config.AAP_API_URL
        self.username = username if username else config.AAP_API_USER
        self.password = password if password else config.AAP_API_PASSWORD

    def retrieve_token(self):
        token = ''
        response = requests.get(self.url, auth=(self.username, self.password))
        if response.ok:
            token = response.text
        return token
