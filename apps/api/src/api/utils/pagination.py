"""
Pagination utilities for audit API.

Implements cursor-based pagination for efficient querying of large datasets.
"""

import base64
import json
from typing import Optional, Dict, Any, List
from datetime import datetime


class PaginationCursor:
    """
    Cursor-based pagination for efficient querying.

    Uses base64-encoded JSON to store pagination state.
    """

    @staticmethod
    def encode(timestamp: datetime, event_id: str) -> str:
        """
        Encode pagination cursor.

        Args:
            timestamp: Last event timestamp
            event_id: Last event ID

        Returns:
            Base64-encoded cursor string
        """
        cursor_data = {
            "timestamp": timestamp.isoformat(),
            "event_id": event_id
        }
        json_str = json.dumps(cursor_data)
        return base64.b64encode(json_str.encode()).decode()

    @staticmethod
    def decode(cursor: str) -> Dict[str, Any]:
        """
        Decode pagination cursor.

        Args:
            cursor: Base64-encoded cursor string

        Returns:
            Dictionary with timestamp and event_id

        Raises:
            ValueError: If cursor is invalid
        """
        try:
            json_str = base64.b64decode(cursor.encode()).decode()
            cursor_data = json.loads(json_str)

            # Parse timestamp
            cursor_data["timestamp"] = datetime.fromisoformat(cursor_data["timestamp"])

            return cursor_data
        except Exception as e:
            raise ValueError(f"Invalid cursor: {e}")


class PaginatedResponse:
    """
    Standardized paginated response structure.
    """

    def __init__(
        self,
        items: List[Any],
        total_count: Optional[int] = None,
        next_cursor: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize paginated response.

        Args:
            items: List of items in current page
            total_count: Total number of items (optional, expensive to compute)
            next_cursor: Cursor for next page
            metadata: Additional metadata about the query
        """
        self.items = items
        self.total_count = total_count
        self.next_cursor = next_cursor
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON response."""
        response = {
            "events": [item.to_dict() if hasattr(item, 'to_dict') else item for item in self.items],
            "count": len(self.items)
        }

        if self.total_count is not None:
            response["total_count"] = self.total_count

        if self.next_cursor:
            response["next_cursor"] = self.next_cursor

        if self.metadata:
            response["query_metadata"] = self.metadata

        return response
