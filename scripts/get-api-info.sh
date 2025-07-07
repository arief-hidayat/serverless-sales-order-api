#!/bin/bash

# Script to retrieve Sales Order API information
# Usage: ./scripts/get-api-info.sh

set -e

echo "🔍 Retrieving Sales Order API Information..."
echo "=============================================="

# Get the stack name from samconfig.toml (use the deploy stack name)
STACK_NAME=$(grep -A 10 '\[default.deploy.parameters\]' samconfig.toml | grep 'stack_name' | cut -d'"' -f2)
echo "📦 Stack Name: $STACK_NAME"

# Get API Gateway URL from CloudFormation outputs
API_URL=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query 'Stacks[0].Outputs[?OutputKey==`SalesOrderApi`].OutputValue' \
    --output text)
echo "🌐 API Base URL: $API_URL"

# Get API Key
API_KEY=$(aws apigateway get-api-keys --include-values --query 'items[0].value' --output text)
echo "🔑 API Key: $API_KEY"

# Get API Key ID and Name for reference
API_KEY_INFO=$(aws apigateway get-api-keys --query 'items[0].{id:id,name:name}' --output table)
echo ""
echo "📋 API Key Details:"
echo "$API_KEY_INFO"

echo ""
echo "🚀 Quick Test Commands:"
echo "======================="
echo "# Health Check (no auth required)"
echo "curl '$API_URL/health'"
echo ""
echo "# List Orders (requires API key)"
echo "curl -H 'X-API-Key: $API_KEY' '$API_URL/orders'"
echo ""
echo "# Swagger UI"
echo "echo 'Open in browser: $API_URL/swagger'"
echo ""
echo "# OpenAPI Specification"
echo "curl '$API_URL/openapi.json'"

echo ""
echo "✅ API Information Retrieved Successfully!"
