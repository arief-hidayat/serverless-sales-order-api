#!/bin/bash

# Simple script to get the API key
# Usage: ./scripts/get-api-key.sh

API_KEY=$(aws apigateway get-api-keys --include-values --query 'items[0].value' --output text)
echo "$API_KEY"
