# File: async-processing/async_sqs_worker.py
# Day 5: Integration of SQS message processing with async patterns

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List
from sqs_client import SQSClient
from async_processor import AsyncDataProcessor

logger = logging.getLogger(__name__)

class AsyncSQSWorker:
    def __init__(self, queue_url: str, worker_id: str = "worker-1"):
        self.sqs_client = SQSClient(queue_url)
        self.processor = AsyncDataProcessor()
        self.worker_id = worker_id
        self.running = False
        self.messages_processed = 0

    async def start_worker(self):
        """Start processing messages from SQS"""
        self.running = True
        logger.info(f"🚀 Starting worker {self.worker_id}")

        while self.running:
            try:
                # Get messages from SQS
                messages = self.sqs_client.receive_messages(max_messages=5)

                if not messages:
                    logger.info("No messages, waiting...")
                    await asyncio.sleep(1)
                    continue

                # Process messages concurrently
                await self._process_messages_batch(messages)

            except KeyboardInterrupt:
                logger.info("Worker shutdown requested")
                self.running = False
            except Exception as e:
                logger.error(f"Worker error: {e}")
                await asyncio.sleep(5)  # Back off on errors

    async def _process_messages_batch(self, messages: List[Dict]):
        """Process a batch of SQS messages"""
        logger.info(f"Processing batch of {len(messages)} messages")

        # Create tasks for concurrent processing
        tasks = [self._process_single_message(msg) for msg in messages]

        # Process all messages concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Count successful processing
        successful = sum(1 for r in results if r is True)
        self.messages_processed += successful

        logger.info(f"Batch complete: {successful}/{len(messages)} successful")

    async def _process_single_message(self, message: Dict) -> bool:
        """Process a single SQS message"""
        receipt_handle = message['ReceiptHandle']

        try:
            # Parse message body
            body = json.loads(message['Body'])
            logger.info(f"Processing sensor {body.get('sensor_id', 'unknown')}")

            # Process the sensor data
            result = await self.processor.process_sensor_reading(body)

            # Here you would store result to database, send to another service, etc.
            logger.debug(f"Processing result: {result['status']}")

            # Delete message from queue after successful processing
            self.sqs_client.delete_message(receipt_handle)

            return True

        except Exception as e:
            logger.error(f"Failed to process message: {e}")
            # Message will be retried or sent to DLQ
            return False

    def get_stats(self) -> Dict:
        """Get worker statistics"""
        return {
            "worker_id": self.worker_id,
            "running": self.running,
            "messages_processed": self.messages_processed
        }

# Simple message producer for testing
class MessageProducer:
    def __init__(self, queue_url: str):
        self.sqs_client = SQSClient(queue_url)

    def send_test_messages(self, count: int = 10):
        """Send test messages to the queue"""
        logger.info(f"Sending {count} test messages")

        for i in range(count):
            message = {
                "sensor_id": i,
                "value": 20 + (i % 30),  # Varying temperature
                "sensor_type": "temperature",
                "location": "Cape Town",
                "timestamp": datetime.now().isoformat()
            }

            try:
                self.sqs_client.send_message(message)
                logger.info(f"Sent message for sensor {i}")
            except Exception as e:
                logger.error(f"Failed to send message {i}: {e}")

# Demo function
async def demo_async_sqs_processing():
    """Demonstrate async SQS processing"""
    # Replace with your actual queue URL
    QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/YOUR-ACCOUNT/geospatial-processing-queue"

    # Send some test messages
    producer = MessageProducer(QUEUE_URL)
    producer.send_test_messages(5)

    # Start a worker to process them
    worker = AsyncSQSWorker(QUEUE_URL, "demo-worker")

    # Run worker for 30 seconds
    try:
        await asyncio.wait_for(worker.start_worker(), timeout=30)
    except asyncio.TimeoutError:
        worker.running = False
        stats = worker.get_stats()
        print(f"Demo complete! Processed {stats['messages_processed']} messages")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(demo_async_sqs_processing())
