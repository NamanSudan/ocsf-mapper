#!/bin/bash

# Create and activate virtual environments for each service
python -m venv backend/ingestion_service/venv
python -m venv backend/classification_service/venv
python -m venv backend/knowledge_base/venv

# Install dependencies
echo "Installing dependencies for ingestion service..."
source backend/ingestion_service/venv/bin/activate
pip install -r backend/ingestion_service/requirements.txt
deactivate

echo "Installing dependencies for classification service..."
source backend/classification_service/venv/bin/activate
pip install -r backend/classification_service/requirements.txt
deactivate

echo "Installing dependencies for knowledge base..."
source backend/knowledge_base/venv/bin/activate
pip install -r backend/knowledge_base/requirements.txt
deactivate

# Setup frontend
echo "Setting up frontend..."
cd frontend
npm install
cd ..

# Copy environment templates
cp infrastructure/docker/env/trieve.env.example infrastructure/docker/env/trieve.env
cp infrastructure/docker/env/clickhouse.env.example infrastructure/docker/env/clickhouse.env
cp infrastructure/docker/env/redis.env.example infrastructure/docker/env/redis.env

echo "Setup complete! Don't forget to configure your environment variables." 