# File: async-processing/sqs_client.py
# Day 5: Essential SQS operations for async message processing

import boto3
import json
import logging
from datetime import datetime
from typing import Dict, List

logger = logging.getLogger(__name__)

class SQSClient:
    def __init__(self, queue_url: str, region: str = 'us-east-1'):
        self.sqs = boto3.client('sqs', region_name=region)
        self.queue_url = queue_url

    def send_message(self, message: Dict) -> str:
        """Send a message to the queue"""
        try:
            response = self.sqs.send_message(
                QueueUrl=self.queue_url,
                MessageBody=json.dumps(message)
            )
            logger.info(f"Message sent: {response['MessageId']}")
            return response['MessageId']
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            raise

    def receive_messages(self, max_messages: int = 1) -> List[Dict]:
        """Receive messages from queue"""
        try:
            response = self.sqs.receive_message(
                QueueUrl=self.queue_url,
                MaxNumberOfMessages=max_messages,
                WaitTimeSeconds=20  # Long polling
            )

            messages = response.get('Messages', [])
            logger.info(f"Received {len(messages)} messages")
            return messages

        except Exception as e:
            logger.error(f"Failed to receive messages: {e}")
            return []

    def delete_message(self, receipt_handle: str):
        """Delete processed message"""
        try:
            self.sqs.delete_message(
                QueueUrl=self.queue_url,
                ReceiptHandle=receipt_handle
            )
            logger.info("Message deleted successfully")
        except Exception as e:
            logger.error(f"Failed to delete message: {e}")

# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Replace with your actual queue URL
    QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/YOUR-ACCOUNT/geospatial-processing-queue"

    client = SQSClient(QUEUE_URL)

    # Send test message
    test_message = {
        "sensor_id": 123,
        "value": 28.5,
        "sensor_type": "temperature",
        "location": "Cape Town",
        "timestamp": datetime.now().isoformat()
    }

    message_id = client.send_message(test_message)
    print(f"Sent message: {message_id}")

    # Receive and process message
    messages = client.receive_messages()
    for message in messages:
        print(f"Received: {message['Body']}")
        client.delete_message(message['ReceiptHandle'])
