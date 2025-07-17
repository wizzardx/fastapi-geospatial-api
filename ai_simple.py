# File: ai_simple.py
# Day 7: Simple AI integration for sensor analysis

import boto3
import json
from datetime import datetime
from typing import Dict, Any

class SimpleAIAnalyzer:
    """Simple AI analyzer using AWS Bedrock"""

    def __init__(self):
        self.bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
        self.model_id = "anthropic.claude-3-haiku-20240307-v1:0"

    def analyze_sensor_data(self, sensor_data: Dict[str, Any]) -> str:
        """Analyze sensor data with AI"""

        # Create a simple prompt
        prompt = f"""
        Analyze this Cape Town sensor data and provide insights:

        Sensor Data: {json.dumps(sensor_data, indent=2)}

        Please provide:
        1. Current conditions summary
        2. Any concerns or alerts
        3. Recommendations for Cape Town city management

        Keep response under 200 words.
        """

        # Format for Claude
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 500,
            "temperature": 0.3,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        try:
            response = self.bedrock.invoke_model(
                body=json.dumps(body),
                modelId=self.model_id,
                accept="application/json",
                contentType="application/json"
            )

            response_body = json.loads(response.get('body').read())
            return response_body.get('content', [{}])[0].get('text', 'No analysis available')

        except Exception as e:
            return f"AI analysis temporarily unavailable: {str(e)}"

# Global analyzer instance
analyzer = SimpleAIAnalyzer()
