import requests

class TogglClient:
    def __init__(self, workspace_id: str, email: str, password: str):
        self.workspace_id = workspace_id

        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})
        self._login(email, password)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.session.close()

    def _login(self, email: str, password: str) -> None:
        AUTH_ENDPOINT = 'https://accounts.toggl.com/api/sessions'
        resp = self.session.post(AUTH_ENDPOINT, json={"email": email, "password": password})
        resp.raise_for_status()

    def get_projects(self):
        PROJECTS_ENDPOINT = f'https://api.track.toggl.com/api/v9/workspaces/{self.workspace_id}/projects'
        resp = self.session.get(PROJECTS_ENDPOINT)
        resp.raise_for_status()
        print(resp.text)

    def get_time_entries(self):
        TIME_ENTRIES_ENDPOINT = "https://api.track.toggl.com/api/v9/me/time_entries"
        resp = self.session.get(TIME_ENTRIES_ENDPOINT)
        resp.raise_for_status()
        print(resp.text)