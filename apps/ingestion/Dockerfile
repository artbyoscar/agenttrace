FROM golang:1.21-alpine AS builder

WORKDIR /app

COPY apps/ingestion/go.mod apps/ingestion/go.sum ./
RUN go mod download

COPY apps/ingestion/ .

RUN CGO_ENABLED=0 GOOS=linux go build -o ingestion .

FROM alpine:latest

RUN apk --no-cache add ca-certificates

WORKDIR /root/

COPY --from=builder /app/ingestion .

EXPOSE 8001

CMD ["./ingestion"]
