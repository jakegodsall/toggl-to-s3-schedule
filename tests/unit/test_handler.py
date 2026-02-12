# tests/unit/test_handler.py
import json
import sys
import os
from datetime import date
from typing import Any
from unittest.mock import MagicMock, patch, call

import pytest

# ---------------------------------------------------------------------------
# Ensure the Lambda source package is importable without a SAM build step.
# The Lambda source lives at toggl-to-s3-schedule/toggl-to-s3-schedule/
# ---------------------------------------------------------------------------
SRC_DIR = os.path.join(
    os.path.dirname(__file__),  # tests/unit/
    "..",                        # tests/
    "..",                        # project root
    "toggl-to-s3-schedule",      # Lambda package directory
)
sys.path.insert(0, os.path.abspath(SRC_DIR))


# ===========================================================================
# TogglClient.get_time_entries tests
# ===========================================================================

class TestGetTimeEntries:
    """get_time_entries must return project_id, not project_name,
    and must NOT call get_project_map."""

    def _make_api_response(self) -> list[dict[str, Any]]:
        return [
            {
                "id": 1001,
                "project_id": 42,
                "description": "Deep work session",
                "start": "2026-02-12T08:00:00+00:00",
                "stop": "2026-02-12T09:30:00+00:00",
                "duration": 5400,
            },
            {
                "id": 1002,
                "project_id": None,
                "description": "Untracked task",
                "start": "2026-02-12T10:00:00+00:00",
                "stop": "2026-02-12T10:45:00+00:00",
                "duration": 2700,
            },
        ]

    def _make_client(self) -> Any:
        """Return a TogglClient with the HTTP session fully mocked."""
        from toggl_client import TogglClient

        with patch("toggl_client.requests.Session") as mock_session_cls:
            mock_session = MagicMock()
            mock_session_cls.return_value = mock_session

            # Mock _login so it doesn't make a real HTTP call.
            login_resp = MagicMock()
            login_resp.raise_for_status.return_value = None
            mock_session.post.return_value = login_resp

            client = TogglClient("ws_123", "user@example.com", "secret")
            client.session = mock_session
            return client

    def test_returns_project_id_field(self) -> None:
        """Each returned entry must contain 'project_id'."""
        client = self._make_client()
        api_response = self._make_api_response()

        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = api_response
        client.session.get.return_value = mock_resp

        entries = client.get_time_entries(date(2026, 2, 12))

        assert entries[0]["project_id"] == 42
        assert entries[1]["project_id"] is None

    def test_does_not_return_project_name_field(self) -> None:
        """Entries must NOT contain a 'project_name' field."""
        client = self._make_client()
        api_response = self._make_api_response()

        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = api_response
        client.session.get.return_value = mock_resp

        entries = client.get_time_entries(date(2026, 2, 12))

        for entry in entries:
            assert "project_name" not in entry

    def test_does_not_call_get_project_map(self) -> None:
        """get_time_entries must not call get_project_map internally."""
        client = self._make_client()
        api_response = self._make_api_response()

        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = api_response
        client.session.get.return_value = mock_resp

        with patch.object(client, "get_project_map") as mock_get_map:
            client.get_time_entries(date(2026, 2, 12))
            mock_get_map.assert_not_called()

    def test_entry_fields_are_correct(self) -> None:
        """Each entry must contain exactly: id, project_id, description, start, stop, duration."""
        client = self._make_client()
        api_response = self._make_api_response()

        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = api_response
        client.session.get.return_value = mock_resp

        entries = client.get_time_entries(date(2026, 2, 12))

        expected_keys = {"id", "project_id", "description", "start", "stop", "duration"}
        for entry in entries:
            assert set(entry.keys()) == expected_keys

    def test_entry_values_match_api_response(self) -> None:
        """Values in the returned entries must match the raw API response."""
        client = self._make_client()
        api_response = self._make_api_response()

        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = api_response
        client.session.get.return_value = mock_resp

        entries = client.get_time_entries(date(2026, 2, 12))

        assert entries[0]["id"] == 1001
        assert entries[0]["description"] == "Deep work session"
        assert entries[0]["start"] == "2026-02-12T08:00:00+00:00"
        assert entries[0]["stop"] == "2026-02-12T09:30:00+00:00"
        assert entries[0]["duration"] == 5400

    def test_returns_empty_list_when_no_entries(self) -> None:
        """An empty API response must return an empty list."""
        client = self._make_client()

        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = []
        client.session.get.return_value = mock_resp

        entries = client.get_time_entries(date(2026, 2, 12))

        assert entries == []

    def test_correct_date_params_sent_to_api(self) -> None:
        """The API request must use start_date and end_date spanning the given day."""
        client = self._make_client()

        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = []
        client.session.get.return_value = mock_resp

        client.get_time_entries(date(2026, 2, 12))

        client.session.get.assert_called_once()
        _, kwargs = client.session.get.call_args
        assert kwargs["params"]["start_date"] == "2026-02-12"
        assert kwargs["params"]["end_date"] == "2026-02-13"


# ===========================================================================
# JSONL serialisation helper tests
# ===========================================================================

class TestSerialiseEntriesToJsonl:
    """The handler exposes a pure helper: serialise_entries_to_jsonl(entries).
    Each entry becomes one JSON line; lines are separated by newlines."""

    def test_single_entry_produces_one_line(self) -> None:
        from app import serialise_entries_to_jsonl

        entries = [
            {
                "id": 1001,
                "project_id": 42,
                "description": "Deep work",
                "start": "2026-02-12T08:00:00+00:00",
                "stop": "2026-02-12T09:30:00+00:00",
                "duration": 5400,
            }
        ]
        result = serialise_entries_to_jsonl(entries)
        lines = result.strip().split("\n")
        assert len(lines) == 1
        assert json.loads(lines[0]) == entries[0]

    def test_multiple_entries_produce_multiple_lines(self) -> None:
        from app import serialise_entries_to_jsonl

        entries = [
            {
                "id": 1001,
                "project_id": 42,
                "description": "Deep work",
                "start": "2026-02-12T08:00:00+00:00",
                "stop": "2026-02-12T09:30:00+00:00",
                "duration": 5400,
            },
            {
                "id": 1002,
                "project_id": None,
                "description": "Untracked",
                "start": "2026-02-12T10:00:00+00:00",
                "stop": "2026-02-12T10:45:00+00:00",
                "duration": 2700,
            },
        ]
        result = serialise_entries_to_jsonl(entries)
        lines = result.strip().split("\n")
        assert len(lines) == 2
        assert json.loads(lines[0]) == entries[0]
        assert json.loads(lines[1]) == entries[1]

    def test_empty_entries_produces_empty_string(self) -> None:
        from app import serialise_entries_to_jsonl

        result = serialise_entries_to_jsonl([])
        assert result == ""

    def test_each_line_is_valid_json(self) -> None:
        from app import serialise_entries_to_jsonl

        entries = [
            {
                "id": i,
                "project_id": i * 10,
                "description": f"Task {i}",
                "start": "2026-02-12T08:00:00+00:00",
                "stop": "2026-02-12T09:00:00+00:00",
                "duration": 3600,
            }
            for i in range(5)
        ]
        result = serialise_entries_to_jsonl(entries)
        for line in result.strip().split("\n"):
            json.loads(line)  # must not raise


# ===========================================================================
# lambda_handler S3 upload tests
# ===========================================================================

class TestLambdaHandlerS3Upload:
    """lambda_handler must upload JSONL to S3 with a date-prefixed key."""

    _FIXED_DATE = date(2026, 2, 12)
    _BUCKET = "my-toggl-bucket"

    def _sample_entries(self) -> list[dict[str, Any]]:
        return [
            {
                "id": 1001,
                "project_id": 42,
                "description": "Deep work",
                "start": "2026-02-12T08:00:00+00:00",
                "stop": "2026-02-12T09:30:00+00:00",
                "duration": 5400,
            }
        ]

    def test_s3_put_object_called_once(self) -> None:
        """handler must call s3_client.put_object exactly once."""
        mock_toggl = MagicMock()
        mock_toggl.__enter__ = MagicMock(return_value=mock_toggl)
        mock_toggl.__exit__ = MagicMock(return_value=False)
        mock_toggl.get_time_entries.return_value = self._sample_entries()

        mock_s3 = MagicMock()

        with patch("app.TogglClient", return_value=mock_toggl), \
             patch("app.date") as mock_date, \
             patch.dict(os.environ, {"S3_BUCKET_NAME": self._BUCKET,
                                     "TOGGL_WORKSPACE": "ws",
                                     "TOGGL_EMAIL": "e@e.com",
                                     "TOGGL_PASSWORD": "pw"}):
            mock_date.today.return_value = self._FIXED_DATE
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)

            from app import lambda_handler
            lambda_handler({}, {}, s3_client=mock_s3)

        mock_s3.put_object.assert_called_once()

    def test_s3_key_has_correct_date_prefix(self) -> None:
        """S3 object key must be '{date}/time_entries.jsonl'."""
        mock_toggl = MagicMock()
        mock_toggl.__enter__ = MagicMock(return_value=mock_toggl)
        mock_toggl.__exit__ = MagicMock(return_value=False)
        mock_toggl.get_time_entries.return_value = self._sample_entries()

        mock_s3 = MagicMock()

        with patch("app.TogglClient", return_value=mock_toggl), \
             patch("app.date") as mock_date, \
             patch.dict(os.environ, {"S3_BUCKET_NAME": self._BUCKET,
                                     "TOGGL_WORKSPACE": "ws",
                                     "TOGGL_EMAIL": "e@e.com",
                                     "TOGGL_PASSWORD": "pw"}):
            mock_date.today.return_value = self._FIXED_DATE
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)

            from app import lambda_handler
            lambda_handler({}, {}, s3_client=mock_s3)

        _, kwargs = mock_s3.put_object.call_args
        assert kwargs["Key"] == "2026-02-12/time_entries.jsonl"

    def test_s3_bucket_name_is_correct(self) -> None:
        """S3 Bucket parameter must match S3_BUCKET_NAME env var."""
        mock_toggl = MagicMock()
        mock_toggl.__enter__ = MagicMock(return_value=mock_toggl)
        mock_toggl.__exit__ = MagicMock(return_value=False)
        mock_toggl.get_time_entries.return_value = self._sample_entries()

        mock_s3 = MagicMock()

        with patch("app.TogglClient", return_value=mock_toggl), \
             patch("app.date") as mock_date, \
             patch.dict(os.environ, {"S3_BUCKET_NAME": self._BUCKET,
                                     "TOGGL_WORKSPACE": "ws",
                                     "TOGGL_EMAIL": "e@e.com",
                                     "TOGGL_PASSWORD": "pw"}):
            mock_date.today.return_value = self._FIXED_DATE
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)

            from app import lambda_handler
            lambda_handler({}, {}, s3_client=mock_s3)

        _, kwargs = mock_s3.put_object.call_args
        assert kwargs["Bucket"] == self._BUCKET

    def test_s3_body_is_valid_jsonl(self) -> None:
        """S3 Body must be valid JSONL matching the fetched entries."""
        entries = self._sample_entries()

        mock_toggl = MagicMock()
        mock_toggl.__enter__ = MagicMock(return_value=mock_toggl)
        mock_toggl.__exit__ = MagicMock(return_value=False)
        mock_toggl.get_time_entries.return_value = entries

        mock_s3 = MagicMock()

        with patch("app.TogglClient", return_value=mock_toggl), \
             patch("app.date") as mock_date, \
             patch.dict(os.environ, {"S3_BUCKET_NAME": self._BUCKET,
                                     "TOGGL_WORKSPACE": "ws",
                                     "TOGGL_EMAIL": "e@e.com",
                                     "TOGGL_PASSWORD": "pw"}):
            mock_date.today.return_value = self._FIXED_DATE
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)

            from app import lambda_handler
            lambda_handler({}, {}, s3_client=mock_s3)

        _, kwargs = mock_s3.put_object.call_args
        body: str = kwargs["Body"]
        lines = body.strip().split("\n")
        assert len(lines) == len(entries)
        for line, expected in zip(lines, entries):
            assert json.loads(line) == expected

    def test_s3_content_type_is_jsonl(self) -> None:
        """S3 ContentType must be 'application/jsonl'."""
        mock_toggl = MagicMock()
        mock_toggl.__enter__ = MagicMock(return_value=mock_toggl)
        mock_toggl.__exit__ = MagicMock(return_value=False)
        mock_toggl.get_time_entries.return_value = self._sample_entries()

        mock_s3 = MagicMock()

        with patch("app.TogglClient", return_value=mock_toggl), \
             patch("app.date") as mock_date, \
             patch.dict(os.environ, {"S3_BUCKET_NAME": self._BUCKET,
                                     "TOGGL_WORKSPACE": "ws",
                                     "TOGGL_EMAIL": "e@e.com",
                                     "TOGGL_PASSWORD": "pw"}):
            mock_date.today.return_value = self._FIXED_DATE
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)

            from app import lambda_handler
            lambda_handler({}, {}, s3_client=mock_s3)

        _, kwargs = mock_s3.put_object.call_args
        assert kwargs["ContentType"] == "application/jsonl"

    def test_handler_returns_200_status_code(self) -> None:
        """handler must return a dict with statusCode 200 on success."""
        mock_toggl = MagicMock()
        mock_toggl.__enter__ = MagicMock(return_value=mock_toggl)
        mock_toggl.__exit__ = MagicMock(return_value=False)
        mock_toggl.get_time_entries.return_value = self._sample_entries()

        mock_s3 = MagicMock()

        with patch("app.TogglClient", return_value=mock_toggl), \
             patch("app.date") as mock_date, \
             patch.dict(os.environ, {"S3_BUCKET_NAME": self._BUCKET,
                                     "TOGGL_WORKSPACE": "ws",
                                     "TOGGL_EMAIL": "e@e.com",
                                     "TOGGL_PASSWORD": "pw"}):
            mock_date.today.return_value = self._FIXED_DATE
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)

            from app import lambda_handler
            response = lambda_handler({}, {}, s3_client=mock_s3)

        assert response["statusCode"] == 200

    def test_handler_response_body_contains_entry_count(self) -> None:
        """handler response body must include the number of entries uploaded."""
        entries = self._sample_entries()

        mock_toggl = MagicMock()
        mock_toggl.__enter__ = MagicMock(return_value=mock_toggl)
        mock_toggl.__exit__ = MagicMock(return_value=False)
        mock_toggl.get_time_entries.return_value = entries

        mock_s3 = MagicMock()

        with patch("app.TogglClient", return_value=mock_toggl), \
             patch("app.date") as mock_date, \
             patch.dict(os.environ, {"S3_BUCKET_NAME": self._BUCKET,
                                     "TOGGL_WORKSPACE": "ws",
                                     "TOGGL_EMAIL": "e@e.com",
                                     "TOGGL_PASSWORD": "pw"}):
            mock_date.today.return_value = self._FIXED_DATE
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)

            from app import lambda_handler
            response = lambda_handler({}, {}, s3_client=mock_s3)

        body = json.loads(response["body"])
        assert body["entries_uploaded"] == len(entries)

    def test_get_time_entries_called_with_today(self) -> None:
        """handler must call get_time_entries with today's date."""
        mock_toggl = MagicMock()
        mock_toggl.__enter__ = MagicMock(return_value=mock_toggl)
        mock_toggl.__exit__ = MagicMock(return_value=False)
        mock_toggl.get_time_entries.return_value = []

        mock_s3 = MagicMock()

        with patch("app.TogglClient", return_value=mock_toggl), \
             patch("app.date") as mock_date, \
             patch.dict(os.environ, {"S3_BUCKET_NAME": self._BUCKET,
                                     "TOGGL_WORKSPACE": "ws",
                                     "TOGGL_EMAIL": "e@e.com",
                                     "TOGGL_PASSWORD": "pw"}):
            mock_date.today.return_value = self._FIXED_DATE
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)

            from app import lambda_handler
            lambda_handler({}, {}, s3_client=mock_s3)

        mock_toggl.get_time_entries.assert_called_once_with(self._FIXED_DATE)
