import json

import os
import requests
import boto3

TOGGL_WORKSPACE_ID = os.environ['TOGGL_WORKSPACE']
TOGGL_EMAIL = os.environ['TOGGL_EMAIL']
TOGGL_PASSWORD = os.environ['TOGGL_PASSWORD']

def lambda_handler(event, context):
    cookie = get_auth_cookie()
    print(cookie)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "hello world",
            # "location": ip.text.replace("\n", "")
        }),
    }

def get_auth_cookie():
    AUTH_ENDPOINT = 'https://accounts.toggl.com/api/sessions'

    headers = {
        "Accept": "application/json"
    }

    body = {
        "email": TOGGL_EMAIL,
        "password": TOGGL_PASSWORD
    }

    resp = requests.post(AUTH_ENDPOINT, headers=headers, json=body)
    resp.raise_for_status()
    return resp.headers['Set-Cookie'].split('=')[-1]

def get_projects(workspace_id: str):
    PROJECTS_ENDPOINT = f'https://api.track.toggl.com/api/v9/workspaces/{workspace_id}/projects'

    headers = {
        "Cookie": "TEST COOKIE",
        "Accept": "application/json"
    }

    resp = requests.get(PROJECTS_ENDPOINT, headers=headers)
    resp.raise_for_status()

    print(resp.text)