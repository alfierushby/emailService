import os
from dotenv import load_dotenv

load_dotenv()

class BaseConfig:
    """Base configuration with shared settings."""
    AWS_REGION = os.getenv("AWS_REGION", "eu-north-1")
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    PRIORITY_QUEUE = os.getenv("P3_QUEUE_URL", "https://prod-queue-url")

    SES_SENDER_EMAIL = os.getenv("SES_SENDER_EMAIL")
    SES_RECIPIENT_EMAIL = os.getenv("SES_RECIPIENT_EMAIL")


class TestConfig(BaseConfig):
    """Test configuration with mock settings"""
    def __init__(self,queue_url):
        self.PRIORITY_QUEUE = queue_url

