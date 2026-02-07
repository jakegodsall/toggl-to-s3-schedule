from typing import Any
from datetime import date, timedelta

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

    def get_project_map(self) -> dict[int, str]:
        PROJECTS_ENDPOINT = f'https://api.track.toggl.com/api/v9/workspaces/{self.workspace_id}/projects'
        resp = self.session.get(PROJECTS_ENDPOINT)
        resp.raise_for_status()
        data = resp.json()

        mapped = {}
        for project in data:
            mapped.update({ project['id']: project['name'] })
        return mapped

    def get_time_entries(self, d: date) -> list[dict[str, Any]]:
        start_date = d.isoformat()                       # "2026-02-07"
        end_date = (d + timedelta(days=1)).isoformat()

        TIME_ENTRIES_ENDPOINT = "https://api.track.toggl.com/api/v9/me/time_entries"
        resp = self.session.get(TIME_ENTRIES_ENDPOINT, params={"start_date": start_date, "end_date": end_date})
        resp.raise_for_status()
        data = resp.json()

        project_map = self.get_project_map()
        entries = []
        for entry in data:
            project_id = entry.get("project_id")
            project_name = project_map.get(project_id) if project_id is not None else None

            entries.append({
                "id": entry["id"],
                "project_name": project_name,
                "description": entry["description"],
                "start": entry["start"],
                "stop": entry["stop"],
                "duration": entry["duration"],
            })
        return entries