# File: database.py
# Day 8: Simple PostgreSQL integration

import os
from databases import Database
from datetime import datetime
from typing import List, Dict, Optional

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/geospatial"
)

database = Database(DATABASE_URL)

class SensorDatabase:
    """Simple database operations for sensors"""

    async def create_sensor_table(self):
        """Create sensors table if it doesn't exist"""
        query = """
        CREATE TABLE IF NOT EXISTS sensors (
            id SERIAL PRIMARY KEY,
            sensor_type VARCHAR(50) NOT NULL,
            value FLOAT NOT NULL,
            location_name VARCHAR(100) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        await database.execute(query)

    async def insert_sensor(self, sensor_type: str, value: float, location_name: str) -> int:
        """Insert sensor reading and return ID"""
        query = """
        INSERT INTO sensors (sensor_type, value, location_name)
        VALUES (:sensor_type, :value, :location_name)
        RETURNING id
        """
        return await database.execute(
            query,
            values={"sensor_type": sensor_type, "value": value, "location_name": location_name}
        )

    async def get_sensors(self, limit: int = 10) -> List[Dict]:
        """Get recent sensor readings"""
        query = """
        SELECT id, sensor_type, value, location_name, created_at
        FROM sensors
        ORDER BY created_at DESC
        LIMIT :limit
        """
        rows = await database.fetch_all(query, values={"limit": limit})
        return [dict(row) for row in rows]

# Global database instance
sensor_db = SensorDatabase()
