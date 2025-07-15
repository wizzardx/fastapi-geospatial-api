# File: async-processing/async_processor.py
# Day 5: Basic async processing patterns with asyncio

import asyncio
import time
import logging
from datetime import datetime
from typing import Dict, List

logger = logging.getLogger(__name__)

class AsyncDataProcessor:
    def __init__(self):
        self.processed_count = 0

    async def process_sensor_reading(self, sensor_data: Dict) -> Dict:
        """Process a single sensor reading asynchronously"""
        start_time = time.time()

        # Simulate I/O-bound operations (database writes, API calls, etc.)
        await asyncio.sleep(0.1)  # Simulated database write
        await asyncio.sleep(0.05)  # Simulated external API call

        # Simple processing logic
        processed_value = sensor_data['value'] * 1.1  # Some calculation
        status = "normal" if sensor_data['value'] < 30 else "alert"

        processing_time = time.time() - start_time
        self.processed_count += 1

        result = {
            "sensor_id": sensor_data['sensor_id'],
            "original_value": sensor_data['value'],
            "processed_value": processed_value,
            "status": status,
            "processing_time_ms": round(processing_time * 1000, 2),
            "processed_at": datetime.now().isoformat()
        }

        logger.info(f"Processed sensor {sensor_data['sensor_id']} in {processing_time:.3f}s")
        return result

    async def process_batch(self, sensor_readings: List[Dict]) -> List[Dict]:
        """Process multiple readings concurrently"""
        logger.info(f"Processing batch of {len(sensor_readings)} readings")
        start_time = time.time()

        # Process all readings concurrently
        tasks = [self.process_sensor_reading(reading) for reading in sensor_readings]
        results = await asyncio.gather(*tasks)

        total_time = time.time() - start_time
        logger.info(f"Batch processed in {total_time:.3f}s")

        return results

# Performance comparison demo
async def compare_sync_vs_async():
    """Demonstrate async performance benefits"""

    # Generate test data
    test_readings = [
        {
            "sensor_id": i,
            "value": 20 + (i % 20),
            "sensor_type": "temperature",
            "location": "Cape Town"
        }
        for i in range(20)
    ]

    processor = AsyncDataProcessor()

    # Time async processing
    start_async = time.time()
    async_results = await processor.process_batch(test_readings)
    async_time = time.time() - start_async

    # Estimate sync time (0.15s per reading sequentially)
    sync_time_estimate = len(test_readings) * 0.15

    print(f"""
    Performance Comparison:
    📊 Readings processed: {len(test_readings)}
    ⚡ Async time: {async_time:.2f}s
    🐌 Sync estimate: {sync_time_estimate:.2f}s
    🚀 Speedup: {sync_time_estimate/async_time:.1f}x faster
    """)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(compare_sync_vs_async())
