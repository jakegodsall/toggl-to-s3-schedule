# Toggl to S3 Schedule

A serverless application that automatically syncs [Toggl Track](https://toggl.com/track/) time entries to Amazon S3 on a daily schedule. Built with AWS SAM and deployed as a Lambda function triggered by EventBridge.

## How It Works

1. An EventBridge rule triggers the Lambda function daily at **3:00 AM UTC**
2. The function authenticates with the Toggl API and fetches time entries for the current day
3. Entries are serialized to [JSONL](https://jsonlines.org/) (JSON Lines) format
4. The file is uploaded to S3 with a date-partitioned key: `YYYY-MM-DD/time_entries.jsonl`

## Project Structure

```
toggl-to-s3-schedule/
├── toggl-to-s3-schedule/       # Lambda function source code
│   ├── app.py                  # Lambda handler and JSONL serialization
│   ├── toggl_client.py         # Toggl API client (session-based auth)
│   └── requirements.txt        # Runtime dependencies
├── tests/
│   └── unit/
│       └── test_handler.py     # Unit tests
├── events/
│   └── event.json              # Sample invocation event
├── template.yaml               # SAM/CloudFormation template
└── samconfig.toml               # SAM CLI configuration
```

## Prerequisites

- [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
- [Python 3.14+](https://www.python.org/downloads/)
- [Docker](https://hub.docker.com/search/?type=edition&offering=community)
- AWS credentials configured (`aws configure`)
- A Toggl Track account with API access
- An existing S3 bucket for storing time entries

## Configuration

The stack requires four parameters, provided at deploy time:

| Parameter | Description |
|---|---|
| `TogglS3BucketName` | Name of the S3 bucket to store time entries |
| `TogglWorkspaceId` | Your Toggl workspace ID |
| `TogglEmail` | Toggl account email |
| `TogglPassword` | Toggl account password |

`TogglWorkspaceId`, `TogglEmail`, and `TogglPassword` are marked `NoEcho` and will not appear in CloudFormation console output.

## Build and Deploy

Build the application:

```bash
sam build --use-container
```

Deploy interactively (first time):

```bash
sam deploy --guided
```

Or deploy with explicit parameters:

```bash
sam deploy \
  --parameter-overrides \
    TogglWorkspaceId=<workspace-id> \
    TogglEmail=<email> \
    TogglPassword='<password>' \
    TogglS3BucketName=<bucket-name>
```

Subsequent deploys (after `samconfig.toml` is saved):

```bash
sam build --use-container && sam deploy
```

## Local Testing

Invoke the function locally:

```bash
sam build --use-container
sam local invoke TogglToS3SyncFunction
```

## Tests

Install test dependencies and run the unit tests:

```bash
pip install -r tests/requirements.txt
python -m pytest tests/unit -v
```

## Logs

Tail logs from the deployed function:

```bash
sam logs -n TogglToS3SyncFunction --stack-name toggl-to-s3-schedule --tail
```

## Cleanup

Delete the deployed stack:

```bash
sam delete --stack-name toggl-to-s3-schedule
```

## Architecture

| Resource | Type | Details |
|---|---|---|
| `TogglToS3SyncFunction` | AWS Lambda | Python 3.14, 90s timeout, x86_64 |
| EventBridge Schedule | ScheduleV2 | `cron(0 3 * * ? *)` |
| IAM Policy | Inline | `s3:PutObject` on the target bucket |

## Technologies

- **Runtime:** Python 3.14 on AWS Lambda
- **Infrastructure:** AWS SAM / CloudFormation
- **Scheduling:** Amazon EventBridge Scheduler
- **Storage:** Amazon S3 (JSONL format)
- **API Client:** `requests` with session-based Toggl authentication
