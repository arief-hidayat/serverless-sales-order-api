# API Key Setup and Testing Guide

This guide explains how to obtain your API key for the Sales Order API and test the functionality using both command line tools and the Swagger UI.

## Table of Contents

- [Getting Your API Key](#getting-your-api-key)
- [Testing with Command Line](#testing-with-command-line)
- [Testing with Swagger UI](#testing-with-swagger-ui)
- [Troubleshooting](#troubleshooting)

## Getting Your API Key

After deploying the Sales Order API, you need to retrieve your API key to access the protected endpoints.

### Method 1: Using AWS CLI (Recommended)

```bash
# Get the API key value
aws apigateway get-api-keys --include-values --query 'items[?name==`sales-order-api-api-key`].value' --output text
```

### Method 2: Using AWS Console

1. Open the [AWS API Gateway Console](https://console.aws.amazon.com/apigateway/)
2. Navigate to **API Keys** in the left sidebar
3. Find the key named `sales-order-api-api-key`
4. Click on the key name
5. Click **Show** next to the API key value
6. Copy the displayed API key

### Method 3: Using CloudFormation Outputs (if configured)

```bash
# Get stack outputs (if API key is exposed in outputs)
aws cloudformation describe-stacks --stack-name sales-order-api --query 'Stacks[0].Outputs'
```

## Testing with Command Line

### Prerequisites

- `curl` command-line tool
- `jq` for JSON formatting (optional but recommended)
- Your API key (obtained from the steps above)

### Basic API Tests

Replace `YOUR_API_KEY_HERE` with your actual API key in the examples below.

#### 1. Test Health Endpoint (No API Key Required)

```bash
curl -s "https://pnhtoi4n69.execute-api.us-east-1.amazonaws.com/Prod/health" | jq '.'
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "SalesOrderAPI",
  "timestamp": "2025-07-07T00:45:00.000Z",
  "version": "1.0.0",
  "orders_count": 0
}
```

#### 2. Test Protected Endpoint Without API Key (Should Fail)

```bash
curl -s "https://pnhtoi4n69.execute-api.us-east-1.amazonaws.com/Prod/orders"
```

**Expected Response:**
```json
{"message":"Forbidden"}
```

#### 3. Test Protected Endpoint With API Key (Should Succeed)

```bash
curl -s -H "X-API-Key: YOUR_API_KEY_HERE" \
  "https://pnhtoi4n69.execute-api.us-east-1.amazonaws.com/Prod/orders" | jq '.'
```

**Expected Response:**
```json
{
  "orders": [],
  "total_count": 0,
  "page": 1,
  "page_size": 10,
  "has_next": false,
  "has_previous": false
}
```

#### 4. Create a Sample Order

```bash
curl -s -X POST \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY_HERE" \
  -d '{
    "customer": {
      "customer_id": "CUST001",
      "first_name": "John",
      "last_name": "Doe",
      "email": "john.doe@example.com",
      "billing_address": {
        "street": "123 Main Street",
        "city": "Anytown",
        "state": "California",
        "postal_code": "12345",
        "country": "USA"
      }
    },
    "items": [
      {
        "item_id": "ITEM001",
        "product_name": "Premium Widget",
        "quantity": 2,
        "unit_price": 29.99
      }
    ],
    "payment_method": "credit_card"
  }' \
  "https://pnhtoi4n69.execute-api.us-east-1.amazonaws.com/Prod/orders" | jq '.'
```

#### 5. List Orders After Creation

```bash
curl -s -H "X-API-Key: YOUR_API_KEY_HERE" \
  "https://pnhtoi4n69.execute-api.us-east-1.amazonaws.com/Prod/orders" | jq '.'
```

## Testing with Swagger UI

The Swagger UI provides an interactive interface to test your API with proper API key authentication.

### Step 1: Access Swagger UI

Open your browser and navigate to:
```
https://pnhtoi4n69.execute-api.us-east-1.amazonaws.com/Prod/swagger
```

### Step 2: Authorize with API Key

1. **Look for the "Authorize" button** at the top right of the Swagger UI interface
2. **Click the "Authorize" button**
3. **Enter your API key** in the "Value" field for ApiKeyAuth
4. **Click "Authorize"** to save the API key
5. **Click "Close"** to return to the main interface

### Step 3: Test Endpoints

Once authorized, you can test any endpoint:

1. **Expand an endpoint** (e.g., `GET /orders`)
2. **Click "Try it out"**
3. **Fill in any required parameters**
4. **Click "Execute"**
5. **View the response** below

### Step 4: Verify Authentication

- **Green lock icons** next to endpoints indicate they require authentication
- **Successfully authenticated requests** will show your API key in the request headers
- **Unauthenticated requests** will return `403 Forbidden` errors

## Automated Testing Script

Use the provided test script for comprehensive API testing:

```bash
# Make the script executable
chmod +x scripts/test-api.sh

# Run the test script
./scripts/test-api.sh
```

The script will:
- Automatically retrieve your API key
- Test all major endpoints
- Validate responses
- Report success/failure for each test

## Troubleshooting

### Common Issues

#### 1. "Forbidden" Error Despite Having API Key

**Problem:** Getting `{"message":"Forbidden"}` even with API key

**Solutions:**
- Verify the API key is correct (no extra spaces or characters)
- Ensure you're using the header name `X-API-Key` (case-sensitive)
- Check that the API key belongs to the correct API Gateway stage

#### 2. API Key Not Found

**Problem:** `aws apigateway get-api-keys` returns empty results

**Solutions:**
- Verify you're in the correct AWS region
- Check your AWS credentials and permissions
- Ensure the CloudFormation stack deployed successfully

#### 3. Swagger UI Not Loading

**Problem:** Swagger UI shows "Loading..." indefinitely

**Solutions:**
- Check browser console for JavaScript errors
- Verify the API Gateway endpoint is accessible
- Try accessing `/openapi.json` directly to test the OpenAPI spec

#### 4. CORS Issues in Browser

**Problem:** Browser blocks requests due to CORS policy

**Solutions:**
- The API is configured with CORS enabled
- If issues persist, try using curl or Postman instead of browser-based tools

### Getting Help

If you encounter issues not covered here:

1. **Check CloudWatch Logs:**
   ```bash
   aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/sales-order-api"
   ```

2. **Verify Stack Status:**
   ```bash
   aws cloudformation describe-stacks --stack-name sales-order-api
   ```

3. **Test Basic Connectivity:**
   ```bash
   curl -s "https://pnhtoi4n69.execute-api.us-east-1.amazonaws.com/Prod/health"
   ```

## Security Best Practices

- **Never commit API keys** to version control
- **Use environment variables** for API keys in scripts
- **Rotate API keys regularly** in production environments
- **Monitor API usage** through CloudWatch metrics
- **Set up usage plans** with appropriate rate limits

## Next Steps

- Explore the complete [API Documentation](../README.md)
- Review [OpenAPI Specification](https://pnhtoi4n69.execute-api.us-east-1.amazonaws.com/Prod/openapi.json)
- Set up monitoring and alerting for your API
- Configure custom domain names for production use
