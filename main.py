# File: main.py
# Day 3: Complete FastAPI geospatial API with async patterns

from fastapi import FastAPI, HTTPException, Query, Path, Depends, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from enum import Enum
import asyncio
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI instance
app = FastAPI(
    title="Geospatial Data API",
    description="Cape Town sensor data processing API",
    version="1.0.0"
)

# Pydantic models (automatic validation)
class Coordinates(BaseModel):
    lat: float
    lng: float

class SensorType(str, Enum):
    temperature = "temperature"
    humidity = "humidity"
    pressure = "pressure"
    air_quality = "air_quality"

class SensorReading(BaseModel):
    sensor_id: int
    value: float
    sensor_type: str
    timestamp: Optional[datetime] = None

class LocationData(BaseModel):
    location: str
    coordinates: Coordinates
    readings: List[SensorReading]

class SensorCreateRequest(BaseModel):
    sensor_type: SensorType
    value: float
    location_name: str = "Cape Town"

class SensorResponse(BaseModel):
    id: int
    sensor_type: SensorType
    value: float
    location_name: str
    created_at: datetime
    status: str = "active"

# In-memory storage
sensor_data_store = []
sensor_id_counter = 1

# Dependency injection functions
def get_current_user():
    """Simulate user authentication"""
    return {"user_id": 1, "username": "cape_town_admin", "role": "admin"}

def get_db_session():
    """Simulate database session"""
    logger.info("Creating DB session...")
    try:
        yield "mock_db_session"
    finally:
        logger.info("Closing DB session...")

# Middleware for timing requests
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"{request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

# Custom exception handler
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    logger.error(f"Value error in {request.url}: {exc}")
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc), "error": str(exc)}
    )

# Background task functions
async def process_sensor_data_async(sensor_id: int):
    """Simulate async data processing"""
    await asyncio.sleep(2)  # Simulate processing time
    logger.info(f"Processed sensor {sensor_id} data")

async def send_alert_async(sensor_id: int, value: float):
    """Simulate sending async alert"""
    await asyncio.sleep(1)
    logger.info(f"Alert sent for sensor {sensor_id}: value {value}")

# API Endpoints

@app.get("/")
async def root():
    return {"message": "Cape Town Geospatial API", "status": "active"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "geospatial-api"
    }

@app.get("/locations/cape-town")
async def get_cape_town_data():
    return LocationData(
        location="Cape Town, South Africa",
        coordinates=Coordinates(lat=-33.9249, lng=18.4241),
        readings=[
            SensorReading(
                sensor_id=1,
                value=23.5,
                sensor_type="temperature",
                timestamp=datetime.now()
            ),
            SensorReading(
                sensor_id=2,
                value=45.2,
                sensor_type="humidity",
                timestamp=datetime.now()
            )
        ]
    )

@app.post("/sensors", response_model=SensorResponse)
async def create_sensor_reading(sensor_data: SensorCreateRequest):
    global sensor_id_counter

    new_reading = SensorResponse(
        id=sensor_id_counter,
        sensor_type=sensor_data.sensor_type,
        value=sensor_data.value,
        location_name=sensor_data.location_name,
        created_at=datetime.now()
    )

    sensor_data_store.append(new_reading)
    sensor_id_counter += 1

    return new_reading

@app.get("/sensors", response_model=List[SensorResponse])
async def list_sensors(
    sensor_type: Optional[SensorType] = Query(None, description="Filter by sensor type"),
    limit: int = Query(10, ge=1, le=100, description="Number of results")
):
    filtered_data = sensor_data_store

    if sensor_type:
        filtered_data = [s for s in filtered_data if s.sensor_type == sensor_type]

    return filtered_data[:limit]

@app.get("/sensors/{sensor_id}", response_model=SensorResponse)
async def get_sensor(sensor_id: int = Path(..., gt=0, description="Sensor ID")):
    sensor = next((s for s in sensor_data_store if s.id == sensor_id), None)

    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")

    return sensor

@app.post("/sensors/process/{sensor_id}")
async def process_sensor(
    sensor_id: int,
    background_tasks: BackgroundTasks
):
    # Find sensor
    sensor = next((s for s in sensor_data_store if s.id == sensor_id), None)
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")

    # Add background processing
    background_tasks.add_task(process_sensor_data_async, sensor_id)

    # Check for alerts (async)
    if sensor.value > 30:  # High temperature alert
        background_tasks.add_task(send_alert_async, sensor_id, sensor.value)

    return {
        "message": f"Processing started for sensor {sensor_id}",
        "status": "queued"
    }

@app.get("/weather/cape-town")
async def get_weather_data():
    """Fetch weather data from external API simulation"""
    # Simulate external API call
    await asyncio.sleep(0.5)

    return {
        "location": "Cape Town",
        "temperature": 22.5,
        "humidity": 68,
        "conditions": "Partly cloudy",
        "wind_speed": 15,
        "source": "simulated_weather_api",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/sensors/validated")
async def create_validated_sensor(sensor_data: SensorCreateRequest):
    # Validation logic - let ValueError bubble up to exception handler
    if sensor_data.value < -50 or sensor_data.value > 100:
        raise ValueError("Sensor value out of valid range (-50 to 100)")

    try:
        # Create sensor
        global sensor_id_counter

        new_reading = SensorResponse(
            id=sensor_id_counter,
            sensor_type=sensor_data.sensor_type,
            value=sensor_data.value,
            location_name=sensor_data.location_name,
            created_at=datetime.now()
        )

        sensor_data_store.append(new_reading)
        sensor_id_counter += 1

        logger.info(f"Created sensor: {sensor_id_counter - 1}")
        return {"sensor_id": sensor_id_counter - 1, "status": "created"}

    except Exception as e:
        logger.error(f"Failed to create sensor: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/admin/sensors")
async def admin_get_sensors(
    current_user: dict = Depends(get_current_user),
    db: str = Depends(get_db_session)
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    return {
        "sensors": sensor_data_store,
        "admin_user": current_user["username"],
        "db_connection": db,
        "total_sensors": len(sensor_data_store)
    }

# Startup and shutdown events
@app.on_event("startup")
async def startup():
    logger.info("FastAPI Geospatial API starting up...")
    logger.info("Database connection would be established here")

@app.on_event("shutdown")
async def shutdown():
    logger.info("FastAPI Geospatial API shutting down...")
    logger.info("Database connection would be closed here")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
