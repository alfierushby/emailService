import json
import os
import threading
import logging

from flask import Flask, jsonify
import boto3
from dotenv import load_dotenv
from prometheus_flask_exporter import PrometheusMetrics, Counter
from pydantic import BaseModel, Field

from config import BaseConfig

stop_event = threading.Event()
load_dotenv()

gunicorn_logger = logging.getLogger("gunicorn.error")

# Want the minimum length to be at least 1, otherwise "" can be sent which breaks certain APIs.
class Request(BaseModel):
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    priority: str = Field(..., min_length=1)


request_counter = Counter(
    "priority_requests_total",
    "Total priority requests processed",
    labelnames=["priority"]
)


def poll_sqs_ses_loop(sqs_client,ses_client,config):
    """
    Constantly checks SQS queue for messages and processes them to send to SES if possible
    """
    while not stop_event.is_set():
        try:
            response = sqs_client.receive_message(
                QueueUrl=config.PRIORITY_QUEUE, WaitTimeSeconds=20)

            messages = response.get("Messages", [])

            if not messages:
                # Use logging instead!!
                gunicorn_logger.info("No messages available")
                continue

            for message in messages:
                receipt_handle = message['ReceiptHandle']
                body = json.loads(message['Body'])

                handled_body = Request(**body).model_dump()

                gunicorn_logger.info(f"Message Body: {handled_body}")

                email_body = (f"Priority: {handled_body['priority']}\nTitle: {handled_body['title']}"
                              f"\nDescription: {handled_body['description']}")

                ses_client.send_email(Source=config.SES_SENDER_EMAIL
                                      , Destination={"ToAddresses": [config.SES_RECIPIENT_EMAIL]}
                                      , Message={
                        "Subject": {"Data": f"P3 Notification: {handled_body['title']}"},
                        "Body": {"Text": {"Data": email_body}}
                    })
                gunicorn_logger.info("Sent email")
                request_counter.labels(priority="High").inc()

                sqs_client.delete_message(QueueUrl=config.PRIORITY_QUEUE, ReceiptHandle=receipt_handle)

        except Exception as e:
            # Use logging instead!!
            gunicorn_logger.info(f"Error, cannot poll: {e}")


def create_app(sqs_client=None,ses_client=None,config=None):
    app = Flask(__name__)
    # Initialize Prometheus Metrics once
    metrics = PrometheusMetrics(app)

    if config is None:
        config = BaseConfig()

    if sqs_client is None:
        sqs_client = boto3.client('sqs', region_name=config.AWS_REGION)
    if ses_client is None:
        ses_client = boto3.client('ses', region_name=config.AWS_REGION)

    sqs_thread = threading.Thread(target=poll_sqs_ses_loop,args=(sqs_client,ses_client,config), daemon=True)
    sqs_thread.start()

    # Store configuration in app config for other entities
    app.config.from_object(config)

    @app.route('/health', methods=["GET"])
    def health_check():
        """ Checks health, endpoint """
        return jsonify({"status": "healthy"}), 200

    return app

if __name__ == '__main__':
    app = create_app().run()
