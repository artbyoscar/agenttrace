package main

import (
	"log"
	"net/http"
	"os"

	"github.com/gorilla/mux"
)

func main() {
	port := os.Getenv("INGESTION_PORT")
	if port == "" {
		port = "8001"
	}

	router := mux.NewRouter()

	// Health check endpoint
	router.HandleFunc("/health", healthCheck).Methods("GET")

	// Ingestion endpoint
	router.HandleFunc("/ingest", ingestTraces).Methods("POST")

	log.Printf("Ingestion service starting on port %s", port)
	if err := http.ListenAndServe(":"+port, router); err != nil {
		log.Fatal(err)
	}
}

func healthCheck(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(`{"status":"healthy"}`))
}

func ingestTraces(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement trace ingestion
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusAccepted)
	w.Write([]byte(`{"message":"Trace accepted for processing"}`))
}
