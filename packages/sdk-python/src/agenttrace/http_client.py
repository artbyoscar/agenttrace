"""HTTP client for AgentTrace API"""

import httpx
from typing import Dict, Any


class HTTPClient:
    """HTTP client for communicating with AgentTrace API"""

    def __init__(self, config):
        self.config = config
        self.client = httpx.Client(
            base_url=config.api_url,
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json",
            },
            timeout=config.timeout,
        )

    def send_trace(self, trace_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send trace data to the API"""
        try:
            response = self.client.post(
                "/api/v1/traces",
                json={
                    **trace_data,
                    "project": self.config.project,
                    "environment": self.config.environment,
                },
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            # TODO: Add proper error handling and retry logic
            print(f"Error sending trace: {e}")
            return {}

    def close(self):
        """Close the HTTP client"""
        self.client.close()
