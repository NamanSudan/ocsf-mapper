#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the script's directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Base URL for the extraction service
BASE_URL="http://localhost:8083"

# Function to make API calls and handle responses
make_request() {
    local endpoint=$1
    local description=$2
    
    echo -e "${BLUE}Extracting ${description}...${NC}"
    
    response=$(curl -s -X POST "${BASE_URL}${endpoint}")
    status=$(echo $response | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
    
    if [ "$status" = "success" ]; then
        echo -e "${GREEN}✓ Successfully extracted ${description}${NC}"
    else
        error=$(echo $response | grep -o '"error":"[^"]*"' | cut -d'"' -f4)
        echo -e "${RED}✗ Failed to extract ${description}: ${error}${NC}"
    fi
    echo
}

# Check if service is healthy
echo -e "${BLUE}Checking service health...${NC}"
health_response=$(curl -s "${BASE_URL}/health")
if [[ $health_response == *"healthy"* ]]; then
    echo -e "${GREEN}✓ Service is healthy${NC}"
    echo
else
    echo -e "${RED}✗ Service is not healthy${NC}"
    exit 1
fi

# Extract all data types
make_request "/extract/ocsf/categories" "categories"
make_request "/extract/ocsf/classes" "classes"
make_request "/extract/ocsf/base-event" "base event"
make_request "/extract/ocsf/schema" "schema"

# Check if files were created
echo -e "${BLUE}Verifying extracted files...${NC}"
DATA_DIR="${SCRIPT_DIR}/../extraction-service/data/ocsf"

check_file() {
    local file=$1
    if [ -f "${DATA_DIR}/${file}" ]; then
        echo -e "${GREEN}✓ ${file} exists${NC}"
        echo -e "${BLUE}File size: $(ls -lh "${DATA_DIR}/${file}" | awk '{print $5}')${NC}"
    else
        echo -e "${RED}✗ ${file} not found${NC}"
    fi
}

check_file "ocsf_categories.json"
check_file "ocsf_classes.json"
check_file "ocsf_base_events.json"
check_file "ocsf_schema.json" 