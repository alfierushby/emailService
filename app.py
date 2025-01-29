import os
import threading

from flask import Flask
import boto3
from dotenv import load_dotenv

load_dotenv()

AWS_REGION = os.getenv('AWS_REGION')
P3_QUEUE_URL = os.getenv('P3_QUEUE_URL')
TEAMS_WEBHOOK_URL = os.getenv('TEAMS_WEBHOOK_URL')
ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
ACCESS_SECRET = os.getenv('AWS_SECRET_ACCESS_KEY')

SES_SENDER_EMAIL = os.getenv("SES_SENDER_EMAIL")
SES_RECIPIENT_EMAIL = os.getenv("SES_RECIPIENT_EMAIL")


app = Flask(__name__)


def poll_sqs_ses_loop():
    """
    Constantly checks SQS queue for messages and processes them to send to SES if possible
    """
    while True:
        try:
            response = sqs_client.receive_message(
                QueueUrl=P3_QUEUE_URL,WaitTimeSeconds=20)

            messages = response.get("Messages",[])

            if not messages:
                print("No messages available")
                continue

            for message in messages:
                receipt_handle = message['ReceiptHandle']
                print(f"Message Body: {message['Body']}")
                message = eval(message['Body'])

                print(f"Message Body: {message}")

                email_body = (f"Priority: {message['priority']}\nTitle: {message['title']}"
                              f"\nDescription: {message['description']}")

                ses_client.send_email(Source=SES_SENDER_EMAIL
                                      ,Destination={"ToAddresses": [SES_RECIPIENT_EMAIL]}
                                      ,Message={
                                            "Subject": {"Data": f"P3 Notification: {message['title']}"},
                                            "Body": {"Text": {"Data": email_body}}
                                        })
                print("Sent email")
                sqs_client.delete_message(QueueUrl=P3_QUEUE_URL,ReceiptHandle=receipt_handle)

        except Exception as e:
            print(f"Error, cannot poll: {e}")



@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'


if __name__ == '__main__':
    sqs_client = boto3.client('sqs', region_name=AWS_REGION, aws_access_key_id=ACCESS_KEY
                              ,aws_secret_access_key=ACCESS_SECRET)
    ses_client = boto3.client('ses', region_name=AWS_REGION, aws_access_key_id=ACCESS_KEY
                              ,aws_secret_access_key=ACCESS_SECRET)

    sqs_thread = threading.Thread(target=poll_sqs_ses_loop, daemon=True)
    sqs_thread.start()
    app.run()
