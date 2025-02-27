import json
import os
import time
from unittest.mock import patch

import boto3
from moto import mock_aws


def test_high_priority_post(client):
    """Test a post to see if it is consumed
     :param client: The client to interact with the app
     """
    # Ensure we use the same region as in mock_env
    sqs = boto3.client("sqs", region_name=os.getenv("AWS_REGION"))

    external_data = {
        "title": "Urgent Issue",
        "description": "Fix ASAP",
        "priority": "High"
    }
    queue_url = client.application.config.get("PRIORITY_QUEUE")
    sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps(external_data))

    # Wait for processing.
    time.sleep(4)
    # Should be empty
    response = sqs.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=10,  # Get up to 10 messages
        WaitTimeSeconds=2,  # Short wait time
        VisibilityTimeout=0  # Ensure messages are visible
    )
    assert "Messages" not in response
