"""
Mock Tool Definitions for Tool Use Tasks

These tool definitions provide the interface specifications that agents
should use when solving tool use tasks. Actual implementations would be
provided by the evaluation environment.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from datetime import datetime


@dataclass
class SearchResult:
    """Result from web search tool."""
    title: str
    url: str
    snippet: str
    relevance_score: float


@dataclass
class APIResponse:
    """Generic API response."""
    status_code: int
    data: Dict[str, Any]
    headers: Dict[str, str]
    timestamp: datetime


# Tool Specifications

WEB_SEARCH_SPEC = {
    "name": "web_search",
    "description": "Search the web for information",
    "parameters": {
        "query": {
            "type": "string",
            "description": "Search query",
            "required": True,
        },
        "max_results": {
            "type": "integer",
            "description": "Maximum number of results to return",
            "default": 10,
            "required": False,
        },
    },
    "returns": {
        "type": "List[SearchResult]",
        "description": "List of search results ordered by relevance",
    },
    "errors": [
        "NetworkError: If search service is unavailable",
        "InvalidQueryError: If query is malformed",
        "RateLimitError: If too many requests in short time",
    ],
    "rate_limit": "10 requests per minute",
}

DATABASE_QUERY_SPEC = {
    "name": "database_query",
    "description": "Execute SQL query on database",
    "parameters": {
        "sql": {
            "type": "string",
            "description": "SQL query to execute",
            "required": True,
        },
        "database": {
            "type": "string",
            "description": "Database name",
            "default": "default",
            "required": False,
        },
    },
    "returns": {
        "type": "DataFrame",
        "description": "Query results as dataframe",
    },
    "errors": [
        "SQLException: If query is invalid",
        "PermissionError: If user lacks access rights",
        "TimeoutError: If query exceeds time limit",
    ],
    "constraints": [
        "Read-only access (SELECT queries only)",
        "5 second query timeout",
    ],
}

API_CALL_SPEC = {
    "name": "api_call",
    "description": "Make HTTP API request",
    "parameters": {
        "endpoint": {
            "type": "string",
            "description": "API endpoint URL",
            "required": True,
        },
        "method": {
            "type": "string",
            "description": "HTTP method",
            "enum": ["GET", "POST", "PUT", "DELETE"],
            "default": "GET",
            "required": False,
        },
        "params": {
            "type": "dict",
            "description": "Query parameters or request body",
            "required": False,
        },
        "headers": {
            "type": "dict",
            "description": "HTTP headers",
            "required": False,
        },
    },
    "returns": {
        "type": "APIResponse",
        "description": "API response with status code and data",
    },
    "errors": [
        "NetworkError: If request fails",
        "AuthenticationError: If auth credentials invalid",
        "RateLimitError: If rate limit exceeded",
        "TimeoutError: If request times out",
    ],
    "rate_limit": "100 requests per hour",
}

FILE_READ_SPEC = {
    "name": "file_read",
    "description": "Read contents of a file",
    "parameters": {
        "path": {
            "type": "string",
            "description": "File path to read",
            "required": True,
        },
        "encoding": {
            "type": "string",
            "description": "File encoding",
            "default": "utf-8",
            "required": False,
        },
    },
    "returns": {
        "type": "string",
        "description": "File contents as string",
    },
    "errors": [
        "FileNotFoundError: If file doesn't exist",
        "PermissionError: If no read permission",
        "UnicodeDecodeError: If encoding is wrong",
    ],
    "constraints": [
        "Maximum file size: 10MB",
    ],
}

FILE_WRITE_SPEC = {
    "name": "file_write",
    "description": "Write contents to a file",
    "parameters": {
        "path": {
            "type": "string",
            "description": "File path to write",
            "required": True,
        },
        "content": {
            "type": "string",
            "description": "Content to write",
            "required": True,
        },
        "mode": {
            "type": "string",
            "description": "Write mode",
            "enum": ["w", "a"],
            "default": "w",
            "required": False,
        },
    },
    "returns": {
        "type": "boolean",
        "description": "True if successful",
    },
    "errors": [
        "PermissionError: If no write permission",
        "DiskFullError: If insufficient disk space",
    ],
}

CALCULATOR_SPEC = {
    "name": "calculator",
    "description": "Evaluate mathematical expression",
    "parameters": {
        "expression": {
            "type": "string",
            "description": "Mathematical expression to evaluate",
            "required": True,
        },
    },
    "returns": {
        "type": "float",
        "description": "Result of calculation",
    },
    "errors": [
        "SyntaxError: If expression is malformed",
        "ZeroDivisionError: If division by zero",
        "OverflowError: If result too large",
    ],
    "supported_operations": [
        "Arithmetic: +, -, *, /, //, %, **",
        "Functions: sin, cos, tan, sqrt, log, exp",
        "Constants: pi, e",
    ],
}

EMAIL_SEND_SPEC = {
    "name": "email_send",
    "description": "Send an email",
    "parameters": {
        "to": {
            "type": "string",
            "description": "Recipient email address",
            "required": True,
        },
        "subject": {
            "type": "string",
            "description": "Email subject",
            "required": True,
        },
        "body": {
            "type": "string",
            "description": "Email body",
            "required": True,
        },
        "cc": {
            "type": "List[string]",
            "description": "CC recipients",
            "required": False,
        },
        "attachments": {
            "type": "List[string]",
            "description": "File paths to attach",
            "required": False,
        },
    },
    "returns": {
        "type": "dict",
        "description": "Send status and message ID",
    },
    "errors": [
        "InvalidEmailError: If email address is invalid",
        "AttachmentTooLargeError: If attachment exceeds 25MB",
        "SMTPError: If email server unavailable",
    ],
}

CODE_EXECUTE_SPEC = {
    "name": "code_execute",
    "description": "Execute Python code in sandbox",
    "parameters": {
        "code": {
            "type": "string",
            "description": "Python code to execute",
            "required": True,
        },
        "timeout": {
            "type": "integer",
            "description": "Execution timeout in seconds",
            "default": 30,
            "required": False,
        },
    },
    "returns": {
        "type": "dict",
        "description": "Execution result with stdout, stderr, return value",
    },
    "errors": [
        "TimeoutError: If execution exceeds timeout",
        "RuntimeError: If code raises exception",
        "SecurityError: If code attempts prohibited operations",
    ],
    "constraints": [
        "No network access",
        "No file system write access",
        "Limited memory (100MB)",
    ],
}

# Collection of all tool specs
ALL_TOOL_SPECS = {
    "web_search": WEB_SEARCH_SPEC,
    "database_query": DATABASE_QUERY_SPEC,
    "api_call": API_CALL_SPEC,
    "file_read": FILE_READ_SPEC,
    "file_write": FILE_WRITE_SPEC,
    "calculator": CALCULATOR_SPEC,
    "email_send": EMAIL_SEND_SPEC,
    "code_execute": CODE_EXECUTE_SPEC,
}


def get_tool_spec(tool_name: str) -> Optional[Dict[str, Any]]:
    """Get specification for a tool by name."""
    return ALL_TOOL_SPECS.get(tool_name)


def get_all_tool_names() -> List[str]:
    """Get list of all available tool names."""
    return list(ALL_TOOL_SPECS.keys())
