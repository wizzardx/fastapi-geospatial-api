# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
```bash
# Run the main FastAPI application
python main.py
# OR
uvicorn main:app --host 0.0.0.0 --port 8000

# Run with Docker
docker-compose up
# Individual service
docker-compose up api
```

### Testing
```bash
# Run all tests
pytest test_main.py -v

# Run tests with coverage (install pytest-cov first)
pytest test_main.py --cov=main

# Run specific test class
pytest test_main.py::TestSensorCRUD -v
```

### Docker Development
```bash
# Build the Docker image
docker build -t fastapi-geospatial-api .

# Run full environment (includes Redis, LocalStack, Nginx)
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

### Async Processing
```bash
# Run async processing demo
python async-processing/async_processor.py

# Run SQS worker (requires AWS credentials or LocalStack)
python async-processing/async_sqs_worker.py
```

## Architecture Overview

This is a FastAPI-based geospatial API for Cape Town sensor data with the following key components:

### Core Application (main.py)
- **FastAPI app** with sensor data CRUD operations
- **Pydantic models** for data validation (SensorReading, LocationData, SensorResponse)
- **Dependency injection** system with simulated auth and database sessions
- **Middleware** for request timing and logging
- **Background tasks** for async sensor processing and alerts
- **Custom exception handlers** for graceful error handling

### Data Models
- `SensorReading`: Core sensor data structure
- `LocationData`: Geospatial location with coordinates and readings
- `SensorResponse`: API response model with metadata
- `SensorType`: Enum for temperature, humidity, pressure, air_quality

### API Endpoints
- `POST /sensors` - Create sensor readings
- `GET /sensors` - List sensors with filtering and pagination
- `GET /sensors/{id}` - Get specific sensor
- `POST /sensors/process/{id}` - Trigger async processing
- `GET /locations/cape-town` - Get Cape Town location data
- `GET /weather/cape-town` - Simulated weather data
- `GET /admin/sensors` - Admin-only endpoint with dependency injection

### Async Processing System (async-processing/)
- **AsyncDataProcessor**: Concurrent sensor data processing
- **SQS integration**: AWS SQS message handling with LocalStack support
- **Performance optimization**: Async patterns for I/O-bound operations

### Infrastructure
- **Docker**: Multi-stage build with security best practices
- **docker-compose**: Full dev environment with Redis, LocalStack, Nginx
- **AWS deployment**: ECS deployment scripts with automated rollback
- **Health checks**: Application and container health monitoring

## Key Dependencies

### Core
- FastAPI 0.104.1 - Web framework
- Pydantic 2.5.0 - Data validation
- Uvicorn 0.24.0 - ASGI server

### Async/Background Processing
- boto3 - AWS SDK for SQS integration
- aiohttp - Async HTTP client
- asyncio - Built-in async support

### Production
- python-json-logger - Structured logging
- prometheus-client - Metrics collection

## Development Notes

### In-Memory Storage
The application uses in-memory lists for sensor data storage with a global counter for IDs. This is suitable for development but should be replaced with a proper database for production.

### Authentication
Uses a simulated authentication system via dependency injection. The `get_current_user()` function returns a mock admin user for testing purposes.

### Error Handling
- Custom ValueError handler returns 422 status with error details
- HTTPException for standard REST API errors
- Comprehensive logging throughout the application

### Testing Strategy
- Uses FastAPI TestClient for integration testing
- Comprehensive test coverage including CRUD operations, validation, middleware, and complete workflows
- Pytest fixtures for data cleanup between tests
- Organized test classes by functionality

### AWS Integration
- LocalStack for local AWS service simulation
- SQS message processing with async workers
- ECS deployment with automated health checks
- Rollback capabilities for production safety

### Container Security
- Non-root user execution
- Multi-stage Docker builds
- Minimal base images
- Health check endpoints