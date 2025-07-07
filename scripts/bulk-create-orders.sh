#!/bin/bash

# Bulk Order Creation Script for Sales Order API
# Usage: ./scripts/bulk-create-orders.sh [orders_file] [api_key]

set -e

# Default values
ORDERS_FILE="${1:-data/sample_orders.json}"
API_KEY="${2:-$(./scripts/get-api-key.sh)}"
BASE_URL="https://pnhtoi4n69.execute-api.us-east-1.amazonaws.com/Prod"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Bulk Order Creation Script${NC}"
echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}📁 Orders file: $ORDERS_FILE${NC}"
echo -e "${BLUE}🔑 API Key: ${API_KEY:0:20}...${NC}"
echo -e "${BLUE}🌐 API URL: $BASE_URL${NC}"
echo ""

# Check if orders file exists
if [ ! -f "$ORDERS_FILE" ]; then
    echo -e "${RED}❌ Error: Orders file '$ORDERS_FILE' not found${NC}"
    echo -e "${YELLOW}💡 Generate sample orders first: python scripts/generate_sample_orders.py${NC}"
    exit 1
fi

# Check if API key is provided
if [ -z "$API_KEY" ]; then
    echo -e "${RED}❌ Error: API key not found${NC}"
    echo -e "${YELLOW}💡 Usage: $0 [orders_file] [api_key]${NC}"
    echo -e "${YELLOW}💡 Or ensure get-api-key.sh script works${NC}"
    exit 1
fi

# Parse JSON and get order count
ORDER_COUNT=$(jq length "$ORDERS_FILE")
echo -e "${BLUE}📊 Found $ORDER_COUNT orders to create${NC}"
echo ""

# Initialize counters
SUCCESS_COUNT=0
FAILED_COUNT=0
CREATED_ORDER_IDS=()

# Create temporary files for results
TEMP_DIR=$(mktemp -d)
SUCCESS_LOG="$TEMP_DIR/success.log"
ERROR_LOG="$TEMP_DIR/error.log"

echo -e "${YELLOW}🔄 Creating orders...${NC}"
echo ""

# Process each order
for i in $(seq 0 $((ORDER_COUNT - 1))); do
    ORDER_JSON=$(jq ".[$i]" "$ORDERS_FILE")
    ORDER_NUM=$((i + 1))
    
    echo -n -e "${BLUE}📦 Creating order $ORDER_NUM/$ORDER_COUNT... ${NC}"
    
    # Make API call
    RESPONSE=$(curl -s -w "\n%{http_code}" \
        -X POST \
        -H "Content-Type: application/json" \
        -H "X-API-Key: $API_KEY" \
        -d "$ORDER_JSON" \
        "$BASE_URL/orders" 2>/dev/null)
    
    # Split response and status code
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    RESPONSE_BODY=$(echo "$RESPONSE" | head -n -1)
    
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "201" ]; then
        ORDER_ID=$(echo "$RESPONSE_BODY" | jq -r '.order_id')
        TOTAL_AMOUNT=$(echo "$RESPONSE_BODY" | jq -r '.total_amount')
        echo -e "${GREEN}✅ Success (ID: ${ORDER_ID:0:8}..., Total: \$${TOTAL_AMOUNT})${NC}"
        
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        CREATED_ORDER_IDS+=("$ORDER_ID")
        echo "$RESPONSE_BODY" >> "$SUCCESS_LOG"
    else
        echo -e "${RED}❌ Failed (HTTP $HTTP_CODE)${NC}"
        FAILED_COUNT=$((FAILED_COUNT + 1))
        echo "Order $ORDER_NUM: HTTP $HTTP_CODE - $RESPONSE_BODY" >> "$ERROR_LOG"
        
        # Show error details for debugging
        if [ "$HTTP_CODE" != "200" ]; then
            ERROR_MSG=$(echo "$RESPONSE_BODY" | jq -r '.message // .error // "Unknown error"' 2>/dev/null || echo "Parse error")
            echo -e "${RED}   Error: $ERROR_MSG${NC}"
        fi
    fi
    
    # Small delay to avoid rate limiting
    sleep 0.1
done

echo ""
echo -e "${BLUE}📊 Bulk Creation Summary${NC}"
echo -e "${BLUE}========================${NC}"
echo -e "${GREEN}✅ Successful: $SUCCESS_COUNT${NC}"
echo -e "${RED}❌ Failed: $FAILED_COUNT${NC}"
echo -e "${BLUE}📈 Success Rate: $(( SUCCESS_COUNT * 100 / ORDER_COUNT ))%${NC}"

if [ $SUCCESS_COUNT -gt 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 Successfully created orders:${NC}"
    for order_id in "${CREATED_ORDER_IDS[@]:0:5}"; do
        echo -e "${GREEN}   - ${order_id}${NC}"
    done
    if [ ${#CREATED_ORDER_IDS[@]} -gt 5 ]; then
        echo -e "${GREEN}   ... and $((${#CREATED_ORDER_IDS[@]} - 5)) more${NC}"
    fi
fi

if [ $FAILED_COUNT -gt 0 ]; then
    echo ""
    echo -e "${RED}❌ Failed orders details:${NC}"
    cat "$ERROR_LOG"
fi

echo ""
echo -e "${BLUE}📁 Detailed logs saved to:${NC}"
echo -e "${BLUE}   Success: $SUCCESS_LOG${NC}"
echo -e "${BLUE}   Errors: $ERROR_LOG${NC}"

echo ""
echo -e "${YELLOW}🔍 Verify results:${NC}"
echo -e "${YELLOW}   curl -H 'X-API-Key: $API_KEY' '$BASE_URL/orders' | jq '.total_count'${NC}"

# Cleanup on exit
trap "rm -rf $TEMP_DIR" EXIT

exit 0
