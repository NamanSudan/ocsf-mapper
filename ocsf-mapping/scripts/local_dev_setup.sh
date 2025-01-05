#!/bin/bash

# Setup local development environment
echo "Setting up local development environment..."

# Copy environment file if it doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file from template"
fi

# Install dependencies for each service
for service in ingestion-service knowledge-base classification-service; do
    echo "Installing dependencies for $service..."
    cd $service && pip install -r requirements.txt && cd ..
done

echo "Setup complete!" 