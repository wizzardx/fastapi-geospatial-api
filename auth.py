# File: auth.py
# Day 8: Simple API authentication

from fastapi import HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os

security = HTTPBearer()

# Simple API key check
VALID_API_KEYS = {
    "dev-key-123": "development",
    "prod-key-456": "production"
}

def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verify API key"""
    api_key = credentials.credentials

    if api_key not in VALID_API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return {"api_key": api_key, "environment": VALID_API_KEYS[api_key]}

# Add to main.py
from auth import verify_api_key

@app.get("/secure/sensors")
async def get_secure_sensors(auth_info = Depends(verify_api_key)):
    """Secured endpoint requiring API key"""
    return {
        "sensors": sensor_data_store,
        "authenticated_as": auth_info["environment"],
        "timestamp": datetime.now().isoformat()
    }
