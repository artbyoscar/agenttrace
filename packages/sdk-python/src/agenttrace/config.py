"""Configuration for AgentTrace SDK"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class Config:
    """Configuration for AgentTrace client"""

    api_key: str
    project: str
    api_url: str = "http://localhost:8000"
    environment: str = "development"
    tags: List[str] = field(default_factory=list)
    enabled: bool = True
    timeout: int = 30
    max_retries: int = 3
    batch_size: int = 10
    flush_interval: int = 5
