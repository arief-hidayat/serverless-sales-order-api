#!/bin/bash

# Sales Order API Test Script
# This script automatically retrieves the API key and tests all major endpoints

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_BASE_URL="https://pnhtoi4n69.execute-api.us-east-1.amazonaws.com/Prod"
API_KEY_NAME="sales-order-api-api-key"
STACK_NAME="sales-order-api"

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_header() {
    echo
    print_status $BLUE "=================================================="
    print_status $BLUE "$1"
    print_status $BLUE "=================================================="
}

print_test() {
    print_status $YELLOW "🧪 Testing: $1"
}

print_success() {
    print_status $GREEN "✅ $1"
}

print_error() {
    print_status $RED "❌ $1"
}

print_info() {
    print_status $BLUE "ℹ️  $1"
}

# Function to check if required tools are installed
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    local missing_tools=()
    
    if ! command -v aws &> /dev/null; then
        missing_tools+=("aws-cli")
    fi
    
    if ! command -v curl &> /dev/null; then
        missing_tools+=("curl")
    fi
    
    if ! command -v jq &> /dev/null; then
        print_info "jq not found - JSON output will not be formatted"
    fi
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        print_error "Missing required tools: ${missing_tools[*]}"
        print_info "Please install the missing tools and try again"
        exit 1
    fi
    
    print_success "All required tools are available"
}

# Function to get API key
get_api_key() {
    print_header "Retrieving API Key"
    
    print_test "Getting API key from AWS API Gateway"
    
    API_KEY=$(aws apigateway get-api-keys --include-values --query "items[?name==\`${API_KEY_NAME}\`].value" --output text 2>/dev/null)
    
    if [ -z "$API_KEY" ] || [ "$API_KEY" == "None" ]; then
        print_error "Failed to retrieve API key"
        print_info "Possible causes:"
        print_info "  - AWS credentials not configured"
        print_info "  - Wrong region selected"
        print_info "  - API key doesn't exist"
        print_info "  - Insufficient permissions"
        
        print_info "Trying alternative method..."
        
        # Try to get from CloudFormation outputs
        API_KEY=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query 'Stacks[0].Outputs[?OutputKey==`ApiKey`].OutputValue' --output text 2>/dev/null)
        
        if [ -z "$API_KEY" ] || [ "$API_KEY" == "None" ]; then
            print_error "Could not retrieve API key using any method"
            print_info "Please manually retrieve your API key using:"
            print_info "  aws apigateway get-api-keys --include-values"
            exit 1
        fi
    fi
    
    print_success "API key retrieved successfully"
    print_info "API Key: ${API_KEY:0:8}...${API_KEY: -4} (masked for security)"
}

# Function to test an endpoint
test_endpoint() {
    local method=$1
    local endpoint=$2
    local description=$3
    local expected_status=$4
    local data=$5
    local use_api_key=$6
    
    print_test "$description"
    
    local curl_cmd="curl -s -w '%{http_code}' -o response.tmp"
    
    if [ "$use_api_key" == "true" ]; then
        curl_cmd="$curl_cmd -H 'X-API-Key: $API_KEY'"
    fi
    
    if [ "$method" != "GET" ]; then
        curl_cmd="$curl_cmd -X $method"
    fi
    
    if [ -n "$data" ]; then
        curl_cmd="$curl_cmd -H 'Content-Type: application/json' -d '$data'"
    fi
    
    curl_cmd="$curl_cmd '$API_BASE_URL$endpoint'"
    
    # Execute the curl command
    local http_code
    http_code=$(eval $curl_cmd)
    local response_body=$(cat response.tmp)
    
    # Check if the response matches expected status
    if [ "$http_code" == "$expected_status" ]; then
        print_success "Status: $http_code (Expected: $expected_status)"
        
        # Pretty print JSON if jq is available
        if command -v jq &> /dev/null && [[ $response_body == {* ]]; then
            echo "$response_body" | jq '.' 2>/dev/null || echo "$response_body"
        else
            echo "$response_body"
        fi
    else
        print_error "Status: $http_code (Expected: $expected_status)"
        echo "Response: $response_body"
        return 1
    fi
    
    # Clean up
    rm -f response.tmp
    echo
}

# Function to run all tests
run_tests() {
    print_header "Running API Tests"
    
    local test_count=0
    local passed_count=0
    
    # Test 1: Health check (no API key required)
    if test_endpoint "GET" "/health" "Health check endpoint" "200" "" "false"; then
        ((passed_count++))
    fi
    ((test_count++))
    
    # Test 2: Protected endpoint without API key (should fail)
    if test_endpoint "GET" "/orders" "Protected endpoint without API key (should fail)" "403" "" "false"; then
        ((passed_count++))
    fi
    ((test_count++))
    
    # Test 3: Protected endpoint with API key (should succeed)
    if test_endpoint "GET" "/orders" "List orders with API key" "200" "" "true"; then
        ((passed_count++))
    fi
    ((test_count++))
    
    # Test 4: OpenAPI specification (no API key required)
    if test_endpoint "GET" "/openapi.json" "OpenAPI specification" "200" "" "false"; then
        ((passed_count++))
    fi
    ((test_count++))
    
    # Test 5: Create a sample order
    local sample_order='{
        "customer": {
            "customer_id": "TEST001",
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "billing_address": {
                "street": "123 Test Street",
                "city": "Test City",
                "state": "Test State",
                "postal_code": "12345",
                "country": "USA"
            }
        },
        "items": [
            {
                "item_id": "ITEM001",
                "product_name": "Test Product",
                "quantity": 1,
                "unit_price": 10.00
            }
        ],
        "payment_method": "credit_card"
    }'
    
    if test_endpoint "POST" "/orders" "Create sample order" "201" "$sample_order" "true"; then
        ((passed_count++))
        CREATED_ORDER_ID=$(cat response.tmp 2>/dev/null | jq -r '.order_id' 2>/dev/null || echo "")
    fi
    ((test_count++))
    
    # Test 6: Get the created order (if creation was successful)
    if [ -n "$CREATED_ORDER_ID" ] && [ "$CREATED_ORDER_ID" != "null" ]; then
        if test_endpoint "GET" "/orders/$CREATED_ORDER_ID" "Get created order" "200" "" "true"; then
            ((passed_count++))
        fi
        ((test_count++))
        
        # Test 7: Update order status
        if test_endpoint "PATCH" "/orders/$CREATED_ORDER_ID/status" "Update order status" "200" '{"status": "confirmed"}' "true"; then
            ((passed_count++))
        fi
        ((test_count++))
    fi
    
    # Test 8: Swagger UI endpoint
    if test_endpoint "GET" "/swagger" "Swagger UI endpoint" "200" "" "false"; then
        ((passed_count++))
    fi
    ((test_count++))
    
    # Print test summary
    print_header "Test Summary"
    print_info "Total tests: $test_count"
    print_info "Passed: $passed_count"
    print_info "Failed: $((test_count - passed_count))"
    
    if [ $passed_count -eq $test_count ]; then
        print_success "All tests passed! 🎉"
        return 0
    else
        print_error "Some tests failed. Please check the output above."
        return 1
    fi
}

# Function to test Swagger UI functionality
test_swagger_ui() {
    print_header "Testing Swagger UI"
    
    print_test "Checking if Swagger UI loads properly"
    
    local swagger_response
    swagger_response=$(curl -s "$API_BASE_URL/swagger")
    
    if echo "$swagger_response" | grep -q "swagger-ui"; then
        print_success "Swagger UI HTML loaded successfully"
    else
        print_error "Swagger UI failed to load"
        return 1
    fi
    
    print_test "Checking if Swagger UI can access OpenAPI spec"
    
    local openapi_response
    openapi_response=$(curl -s "$API_BASE_URL/swagger?format=json")
    
    if echo "$openapi_response" | grep -q "securitySchemes"; then
        print_success "OpenAPI spec with security schemes accessible"
    else
        print_error "OpenAPI spec missing security configuration"
        return 1
    fi
    
    print_info "Swagger UI URL: $API_BASE_URL/swagger"
    print_info "To test in browser:"
    print_info "  1. Open: $API_BASE_URL/swagger"
    print_info "  2. Click 'Authorize' button"
    print_info "  3. Enter API key: $API_KEY"
    print_info "  4. Test any protected endpoint"
}

# Function to show usage instructions
show_usage() {
    print_header "Sales Order API Test Results"
    
    print_info "Your API is ready to use! Here's how to get started:"
    echo
    print_info "🔑 API Key: $API_KEY"
    print_info "🌐 Base URL: $API_BASE_URL"
    print_info "📚 Swagger UI: $API_BASE_URL/swagger"
    print_info "📋 OpenAPI Spec: $API_BASE_URL/openapi.json"
    echo
    print_info "Quick test commands:"
    echo "  # Test health endpoint (no auth required)"
    echo "  curl '$API_BASE_URL/health'"
    echo
    echo "  # List orders (requires API key)"
    echo "  curl -H 'X-API-Key: $API_KEY' '$API_BASE_URL/orders'"
    echo
    echo "  # Create an order (requires API key)"
    echo "  curl -X POST -H 'Content-Type: application/json' -H 'X-API-Key: $API_KEY' \\"
    echo "    -d '{\"customer\":{...}, \"items\":[...], \"payment_method\":\"credit_card\"}' \\"
    echo "    '$API_BASE_URL/orders'"
    echo
    print_info "For detailed documentation, see: docs/API_KEY_SETUP.md"
}

# Main execution
main() {
    print_header "Sales Order API Test Suite"
    print_info "This script will test your Sales Order API functionality"
    echo
    
    # Check prerequisites
    check_prerequisites
    
    # Get API key
    get_api_key
    
    # Run tests
    if run_tests; then
        test_swagger_ui
        show_usage
        exit 0
    else
        print_error "Tests failed. Please check your API configuration."
        exit 1
    fi
}

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [options]"
        echo "Options:"
        echo "  --help, -h    Show this help message"
        echo "  --key-only    Only retrieve and display the API key"
        echo "  --test-only   Run tests with existing API key (set API_KEY env var)"
        exit 0
        ;;
    --key-only)
        check_prerequisites
        get_api_key
        echo "$API_KEY"
        exit 0
        ;;
    --test-only)
        if [ -z "${API_KEY:-}" ]; then
            print_error "API_KEY environment variable not set"
            print_info "Usage: API_KEY=your-key-here $0 --test-only"
            exit 1
        fi
        run_tests
        exit $?
        ;;
    "")
        main
        ;;
    *)
        print_error "Unknown option: $1"
        print_info "Use --help for usage information"
        exit 1
        ;;
esac
