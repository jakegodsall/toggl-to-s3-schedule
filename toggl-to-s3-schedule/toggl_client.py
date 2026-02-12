# toggl-to-s3-schedule/toggl_client.py
from typing import Any, Optional
from datetime import date, timedelta

import requests


class TogglClient:
    def __init__(self, workspace_id: str, email: str, password: str) -> None:
        self.workspace_id = workspace_id
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})
        self._login(email, password)

    def __enter__(self) -> "TogglClient":
        return self

    def __exit__(
        self,
        exc_type: Optional[type],
        exc: Optional[BaseException],
        tb: Optional[object],
    ) -> None:
        self.session.close()

    def _login(self, email: str, password: str) -> None:
        AUTH_ENDPOINT = "https://accounts.toggl.com/api/sessions"
        resp = self.session.post(AUTH_ENDPOINT, json={"email": email, "password": password})
        resp.raise_for_status()

    def get_project_map(self) -> dict[int, str]:
        """Return a mapping of project_id -> project_name for this workspace."""
        PROJECTS_ENDPOINT = (
            f"https://api.track.toggl.com/api/v9/workspaces/{self.workspace_id}/projects"
        )
        resp = self.session.get(PROJECTS_ENDPOINT)
        resp.raise_for_status()
        data: list[dict[str, Any]] = resp.json()
        return {project["id"]: project["name"] for project in data}

    def get_time_entries(self, d: date) -> list[dict[str, Any]]:
        """Return time entries for the given date.

        Each entry contains: id, project_id, description, start, stop, duration.
        project_id is taken directly from the Toggl API response (may be None).
        """
        start_date = d.isoformat()
        end_date = (d + timedelta(days=1)).isoformat()

        TIME_ENTRIES_ENDPOINT = "https://api.track.toggl.com/api/v9/me/time_entries"
        resp = self.session.get(
            TIME_ENTRIES_ENDPOINT,
            params={"start_date": start_date, "end_date": end_date},
        )
        resp.raise_for_status()
        data: list[dict[str, Any]] = resp.json()

        return [
            {
                "id": entry["id"],
                "project_id": entry.get("project_id"),
                "description": entry["description"],
                "start": entry["start"],
                "stop": entry["stop"],
                "duration": entry["duration"],
            }
            for entry in data
        ]
