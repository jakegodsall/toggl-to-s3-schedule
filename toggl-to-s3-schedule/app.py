import json

import os
import requests
import boto3
from datetime import date

from toggl_client import TogglClient

TOGGL_WORKSPACE_ID = os.environ['TOGGL_WORKSPACE']
TOGGL_EMAIL = os.environ['TOGGL_EMAIL']
TOGGL_PASSWORD = os.environ['TOGGL_PASSWORD']

def lambda_handler(event, context):
    with TogglClient(TOGGL_WORKSPACE_ID, TOGGL_EMAIL, TOGGL_PASSWORD) as toggl:
        entries = toggl.get_time_entries(date.today())
        print(entries)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "hello world",
            # "location": ip.text.replace("\n", "")
        }),
    }