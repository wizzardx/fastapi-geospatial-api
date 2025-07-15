# File: test_main.py
# Day 3: Complete test suite for FastAPI geospatial API

import pytest
from fastapi.testclient import TestClient
from main import app

# Create test client
client = TestClient(app)

class TestBasicEndpoints:
    """Test basic API endpoints"""

    def test_root_endpoint(self):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "Cape Town" in data["message"]
        assert data["status"] == "active"

    def test_health_check(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["service"] == "geospatial-api"

    def test_cape_town_location_data(self):
        response = client.get("/locations/cape-town")
        assert response.status_code == 200
        data = response.json()
        assert data["location"] == "Cape Town, South Africa"
        assert data["coordinates"]["lat"] == -33.9249
        assert data["coordinates"]["lng"] == 18.4241
        assert len(data["readings"]) == 2

    def test_weather_endpoint(self):
        response = client.get("/weather/cape-town")
        assert response.status_code == 200
        data = response.json()
        assert data["location"] == "Cape Town"
        assert "temperature" in data
        assert "humidity" in data
        assert data["source"] == "simulated_weather_api"


class TestSensorCRUD:
    """Test sensor CRUD operations"""

    def test_create_sensor_valid_data(self):
        sensor_data = {
            "sensor_type": "temperature",
            "value": 25.5,
            "location_name": "Cape Town"
        }
        response = client.post("/sensors", json=sensor_data)
        assert response.status_code == 200
        data = response.json()
        assert data["sensor_type"] == "temperature"
        assert data["value"] == 25.5
        assert data["location_name"] == "Cape Town"
        assert data["status"] == "active"
        assert "id" in data
        assert "created_at" in data

    def test_create_sensor_minimal_data(self):
        sensor_data = {
            "sensor_type": "humidity",
            "value": 68.2
        }
        response = client.post("/sensors", json=sensor_data)
        assert response.status_code == 200
        data = response.json()
        assert data["sensor_type"] == "humidity"
        assert data["location_name"] == "Cape Town"  # Default value

    def test_create_sensor_invalid_type(self):
        sensor_data = {
            "sensor_type": "invalid_type",
            "value": 25.5
        }
        response = client.post("/sensors", json=sensor_data)
        assert response.status_code == 422  # Validation error

    def test_list_sensors_default(self):
        # First create a sensor
        sensor_data = {
            "sensor_type": "pressure",
            "value": 1013.25
        }
        client.post("/sensors", json=sensor_data)

        # Then list sensors
        response = client.get("/sensors")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_list_sensors_with_filter(self):
        # Create sensors of different types
        client.post("/sensors", json={"sensor_type": "temperature", "value": 20.0})
        client.post("/sensors", json={"sensor_type": "humidity", "value": 50.0})

        # Filter by temperature
        response = client.get("/sensors?sensor_type=temperature")
        assert response.status_code == 200
        data = response.json()
        assert all(sensor["sensor_type"] == "temperature" for sensor in data)

    def test_list_sensors_with_limit(self):
        response = client.get("/sensors?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 5

    def test_get_sensor_by_id(self):
        # Create a sensor first
        sensor_data = {"sensor_type": "air_quality", "value": 85.0}
        create_response = client.post("/sensors", json=sensor_data)
        sensor_id = create_response.json()["id"]

        # Get the sensor by ID
        response = client.get(f"/sensors/{sensor_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sensor_id
        assert data["sensor_type"] == "air_quality"

    def test_get_sensor_not_found(self):
        response = client.get("/sensors/99999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_sensor_invalid_id(self):
        response = client.get("/sensors/0")  # ID must be > 0
        assert response.status_code == 422


class TestSensorValidation:
    """Test sensor validation endpoints"""

    def test_create_validated_sensor_valid(self):
        sensor_data = {
            "sensor_type": "temperature",
            "value": 25.0
        }
        response = client.post("/sensors/validated", json=sensor_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "created"
        assert "sensor_id" in data

    def test_create_validated_sensor_value_too_high(self):
        sensor_data = {
            "sensor_type": "temperature",
            "value": 150.0  # Too high
        }
        response = client.post("/sensors/validated", json=sensor_data)
        assert response.status_code == 422
        assert "out of valid range" in response.json()["detail"]

    def test_create_validated_sensor_value_too_low(self):
        sensor_data = {
            "sensor_type": "temperature",
            "value": -100.0  # Too low
        }
        response = client.post("/sensors/validated", json=sensor_data)
        assert response.status_code == 422
        assert "out of valid range" in response.json()["detail"]


class TestSensorProcessing:
    """Test sensor processing endpoints"""

    def test_process_sensor_valid_id(self):
        # Create a sensor first
        sensor_data = {"sensor_type": "temperature", "value": 35.0}
        create_response = client.post("/sensors", json=sensor_data)
        sensor_id = create_response.json()["id"]

        # Process the sensor
        response = client.post(f"/sensors/process/{sensor_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "queued"
        assert f"sensor {sensor_id}" in data["message"]

    def test_process_sensor_not_found(self):
        response = client.post("/sensors/process/99999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestAdminEndpoints:
    """Test admin-only endpoints"""

    def test_admin_get_sensors(self):
        response = client.get("/admin/sensors")
        assert response.status_code == 200
        data = response.json()
        assert "sensors" in data
        assert "admin_user" in data
        assert data["admin_user"] == "cape_town_admin"
        assert "total_sensors" in data
        assert isinstance(data["sensors"], list)


class TestMiddleware:
    """Test middleware functionality"""

    def test_process_time_header(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert "X-Process-Time" in response.headers
        # Process time should be a float value
        process_time = float(response.headers["X-Process-Time"])
        assert process_time >= 0


class TestDataValidation:
    """Test various data validation scenarios"""

    def test_sensor_type_enum_validation(self):
        valid_types = ["temperature", "humidity", "pressure", "air_quality"]

        for sensor_type in valid_types:
            sensor_data = {
                "sensor_type": sensor_type,
                "value": 25.0
            }
            response = client.post("/sensors", json=sensor_data)
            assert response.status_code == 200

    def test_missing_required_fields(self):
        # Missing sensor_type
        response = client.post("/sensors", json={"value": 25.0})
        assert response.status_code == 422

        # Missing value
        response = client.post("/sensors", json={"sensor_type": "temperature"})
        assert response.status_code == 422

    def test_invalid_data_types(self):
        # Invalid value type
        sensor_data = {
            "sensor_type": "temperature",
            "value": "not_a_number"
        }
        response = client.post("/sensors", json=sensor_data)
        assert response.status_code == 422


class TestQueryParameters:
    """Test query parameter validation"""

    def test_sensors_limit_validation(self):
        # Valid limits
        response = client.get("/sensors?limit=1")
        assert response.status_code == 200

        response = client.get("/sensors?limit=100")
        assert response.status_code == 200

        # Invalid limits
        response = client.get("/sensors?limit=0")
        assert response.status_code == 422

        response = client.get("/sensors?limit=101")
        assert response.status_code == 422


# Fixtures for test data cleanup
@pytest.fixture(autouse=True)
def reset_sensor_data():
    """Reset sensor data before each test"""
    from main import sensor_data_store, sensor_id_counter
    sensor_data_store.clear()
    # Note: We can't easily reset the counter without modifying the app structure


# Integration tests
class TestIntegration:
    """Test complete workflows"""

    def test_complete_sensor_workflow(self):
        """Test creating, listing, getting, and processing a sensor"""
        # Create sensor
        sensor_data = {
            "sensor_type": "temperature",
            "value": 28.5,
            "location_name": "Cape Town Waterfront"
        }
        create_response = client.post("/sensors", json=sensor_data)
        assert create_response.status_code == 200
        sensor_id = create_response.json()["id"]

        # List sensors (should include our new one)
        list_response = client.get("/sensors")
        assert list_response.status_code == 200
        sensor_ids = [s["id"] for s in list_response.json()]
        assert sensor_id in sensor_ids

        # Get specific sensor
        get_response = client.get(f"/sensors/{sensor_id}")
        assert get_response.status_code == 200
        assert get_response.json()["id"] == sensor_id

        # Process sensor
        process_response = client.post(f"/sensors/process/{sensor_id}")
        assert process_response.status_code == 200
        assert process_response.json()["status"] == "queued"


if __name__ == "__main__":
    # Run tests with: python test_main.py
    # Or better: pip install pytest && pytest test_main.py -v
    pytest.main([__file__, "-v"])
