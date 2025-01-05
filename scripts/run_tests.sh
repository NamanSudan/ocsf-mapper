#!/bin/bash

# Run all tests across services
echo "Running tests..."

for service in ingestion-service knowledge-base classification-service; do
    echo "Testing $service..."
    cd $service && python -m pytest && cd ..
done 