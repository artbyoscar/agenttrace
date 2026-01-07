# AgentTrace Ingestion Service

High-performance ingestion service for processing trace data.

## Overview

The ingestion service is responsible for:
- Receiving trace data from SDKs
- Validating and processing traces
- Publishing to message queue (Kafka)
- High-throughput data ingestion

## Tech Stack

- Go 1.21+
- Kafka for message queueing
- Gorilla Mux for routing

## Setup

1. Install Go dependencies:
```bash
go mod download
```

2. Configure environment:
```bash
export INGESTION_PORT=8001
export KAFKA_BOOTSTRAP_SERVERS=localhost:9092
```

3. Run the service:
```bash
go run main.go
```

## Building

```bash
go build -o ingestion .
./ingestion
```

## Docker

```bash
docker build -t agenttrace-ingestion -f Dockerfile ../..
docker run -p 8001:8001 agenttrace-ingestion
```

## API Endpoints

- `GET /health` - Health check
- `POST /ingest` - Ingest trace data

## Performance

The ingestion service is designed for high throughput:
- Non-blocking I/O
- Batch processing
- Message queue integration
- Horizontal scalability
