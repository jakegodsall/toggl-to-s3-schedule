import requests

class TogglClient:
    def __init__(self, workspace_id: str, email: str, password: str):
        self.workspace_id = workspace_id

        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})
        self._login(email, password)

    def _login(self, email: str, password: str) -> None:
        AUTH_ENDPOINT = 'https://accounts.toggl.com/api/sessions'
        resp = self.session.get(AUTH_ENDPOINT, json={"email": email, "password": password})
        resp.raise_for_status()