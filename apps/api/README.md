# AgentTrace API

FastAPI backend for AgentTrace.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

2. Configure environment:
```bash
cp ../../.env.example .env
# Edit .env with your configuration
```

3. Run the API:
```bash
python main.py
```

Or with uvicorn:
```bash
uvicorn main:app --reload
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

```bash
pytest tests/
```

## Project Structure

```
api/
├── main.py              # Application entry point
├── src/
│   ├── api/
│   │   └── routes/      # API endpoints
│   ├── models/          # Database models
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # Business logic
│   └── config.py        # Configuration
└── tests/               # Test files
```
