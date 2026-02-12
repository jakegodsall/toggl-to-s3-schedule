# toggl-to-s3-schedule/app.py
import json
import os
from datetime import date
from typing import Any, Optional

import boto3

from toggl_client import TogglClient


def serialise_entries_to_jsonl(entries: list[dict[str, Any]]) -> str:
    """Serialise a list of entry dicts to JSONL format.

    Each entry is encoded as a JSON object on its own line.
    Returns an empty string when the list is empty.
    """
    if not entries:
        return ""
    return "\n".join(json.dumps(entry) for entry in entries)


def lambda_handler(
    event: dict[str, Any],
    context: Any,
    s3_client: Optional[Any] = None,
) -> dict[str, Any]:
    """Fetch today's Toggl time entries and upload them to S3 as JSONL.

    The S3 object key follows the pattern: ``{YYYY-MM-DD}/time_entries.jsonl``.
    """
    toggl_workspace_id: str = os.environ["TOGGL_WORKSPACE"]
    toggl_email: str = os.environ["TOGGL_EMAIL"]
    toggl_password: str = os.environ["TOGGL_PASSWORD"]
    s3_bucket_name: str = os.environ["S3_BUCKET_NAME"]

    client: Any = s3_client or boto3.client("s3")

    today: date = date.today()

    with TogglClient(toggl_workspace_id, toggl_email, toggl_password) as toggl:
        entries: list[dict[str, Any]] = toggl.get_time_entries(today)

    jsonl_body: str = serialise_entries_to_jsonl(entries)
    s3_key: str = f"{today.isoformat()}/time_entries.jsonl"

    client.put_object(
        Bucket=s3_bucket_name,
        Key=s3_key,
        Body=jsonl_body,
        ContentType="application/jsonl",
    )

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "entries_uploaded": len(entries),
                "s3_key": s3_key,
            }
        ),
    }
