# Sales Order API

A comprehensive RESTful API for managing sales orders with full CRUD operations, built with AWS Lambda Powertools for observability and Pydantic for data validation. This API is specifically designed to be AI-agent friendly with extensive documentation, validation, and error handling.

## Features

- **Complete Order Management**: Create, read, update, and delete sales orders
- **Customer Management**: Full customer information with billing and shipping addresses  
- **Item Management**: Detailed order items with pricing, discounts, and tax calculations
- **Status Tracking**: Order status management throughout the fulfillment process
- **Data Validation**: Comprehensive validation using Pydantic models
- **Error Handling**: Consistent error responses with detailed information
- **Observability**: Built-in logging, tracing, and metrics with AWS Lambda Powertools
- **OpenAPI Documentation**: Complete OpenAPI 3.0 specification for AI agents
- **In-Memory Storage**: Development-ready storage (easily replaceable with database)

## Architecture

This serverless application uses:

- **AWS Lambda**: Serverless compute for API endpoints
- **API Gateway**: RESTful API management and routing
- **AWS X-Ray**: Distributed tracing for observability
- **CloudWatch**: Logging and custom metrics
- **AWS Lambda Powertools**: Enhanced observability and utilities
- **Pydantic**: Data validation and serialization
- **Python 3.13**: Latest Python runtime

## Security

This API uses **API Key authentication** to secure all order management endpoints. The health check (`/health`) and OpenAPI specification (`/openapi.json`) endpoints are publicly accessible for monitoring purposes.

### Authentication

To access protected endpoints, include your API key in the request header:

```bash
X-API-Key: your-api-key-here
```

### Rate Limiting

The API includes built-in rate limiting:
- **Rate Limit**: 50 requests per second
- **Burst Limit**: 100 requests  
- **Monthly Quota**: 10,000 requests per month

### Getting Your API Key

After deployment, your API key will be displayed in the CloudFormation outputs. You can also retrieve it using:

```bash
aws apigateway get-api-keys --include-values
```

## API Endpoints

### Order Management
- `POST /orders` - Create a new sales order
- `GET /orders` - List orders with pagination and filtering
- `GET /orders/{order_id}` - Get a specific order
- `PUT /orders/{order_id}` - Update an existing order
- `DELETE /orders/{order_id}` - Delete an order

### Order Status
- `GET /orders/{order_id}/status` - Get order status
- `PATCH /orders/{order_id}/status` - Update order status only

### Utility
- `GET /health` - Health check endpoint
- `GET /openapi.json` - OpenAPI 3.0 specification

## Order Lifecycle

1. **Draft**: Order is being created but not yet submitted
2. **Pending**: Order submitted and awaiting processing
3. **Confirmed**: Order confirmed and being prepared
4. **Shipped**: Order has been shipped to customer
5. **Delivered**: Order successfully delivered to customer
6. **Cancelled**: Order was cancelled before fulfillment
7. **Returned**: Order was returned by customer

## Data Models

### Customer
Complete customer information including:
- Personal details (name, email, phone)
- Billing address (required)
- Shipping address (optional, defaults to billing)

### Order Item
Individual items within an order:
- Product information (ID, name, SKU)
- Quantity and unit pricing
- Discount and tax percentages
- Automatic total calculations

### Sales Order
Complete order with:
- Unique order ID and optional order number
- Customer information
- List of order items
- Order status and payment method
- Delivery dates and notes
- Automatic pricing calculations

## AI Agent Integration

This API is specifically designed for AI agent integration with:

- **Comprehensive Documentation**: Every field, endpoint, and operation is thoroughly documented
- **Clear Validation Rules**: Explicit validation constraints and error messages
- **Consistent Response Formats**: Standardized response structures across all endpoints
- **Detailed Error Information**: Specific error types and troubleshooting details
- **Business Logic Documentation**: Clear explanation of order lifecycle and calculations
- **OpenAPI Specification**: Machine-readable API documentation

## Getting Started

### Prerequisites

- [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) configured with your credentials
- [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html) installed
- [Python 3.13](https://www.python.org/downloads/) installed
- [Docker](https://hub.docker.com/search/?type=edition&offering=community) for local testing

### Installation

1. **Clone or navigate to the project directory**:
   ```bash
   cd sam-app
   ```

2. **Install dependencies**:
   ```bash
   pip install -r sales_order_api/requirements.txt
   ```

3. **Build the application**:
   ```bash
   sam build --use-container
   ```

### Local Development

1. **Start the API locally**:
   ```bash
   sam local start-api
   ```

2. **Test the API**:
   ```bash
   # Health check
   curl http://localhost:3000/health
   
   # Get OpenAPI specification
   curl http://localhost:3000/openapi.json
   
   # Create a sample order
   curl -X POST http://localhost:3000/orders \
     -H "Content-Type: application/json" \
     -d '{
       "customer": {
         "customer_id": "CUST001",
         "first_name": "John",
         "last_name": "Doe",
         "email": "john.doe@example.com",
         "billing_address": {
           "street": "123 Main St",
           "city": "Anytown",
           "state": "CA",
           "postal_code": "12345",
           "country": "USA"
         }
       },
       "items": [{
         "item_id": "ITEM001",
         "product_name": "Widget A",
         "quantity": 2,
         "unit_price": 29.99
       }],
       "payment_method": "credit_card"
     }'
   ```

### Deployment

1. **Deploy to AWS**:
   ```bash
   sam deploy --guided
   ```

2. **Follow the prompts**:
   - **Stack Name**: Choose a unique name (e.g., `sales-order-api`)
   - **AWS Region**: Select your preferred region
   - **Environment**: Choose `dev`, `staging`, or `prod`
   - **Confirm changes**: Review before deployment
   - **Allow IAM role creation**: Required for Lambda execution
   - **Save parameters**: Save configuration for future deployments

3. **Note the API endpoint** from the deployment output

## API Usage Examples

### Create an Order

```bash
curl -X POST https://your-api-gateway-url/orders \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{
    "customer": {
      "customer_id": "CUST001",
      "first_name": "Jane",
      "last_name": "Smith",
      "email": "jane.smith@example.com",
      "phone": "+1-555-123-4567",
      "billing_address": {
        "street": "456 Oak Avenue",
        "city": "Somewhere",
        "state": "NY",
        "postal_code": "67890",
        "country": "USA"
      }
    },
    "items": [
      {
        "item_id": "WIDGET001",
        "product_name": "Premium Widget",
        "sku": "WDG-PREM-001",
        "quantity": 2,
        "unit_price": 29.99,
        "discount_percent": 10.0,
        "tax_percent": 8.25
      }
    ],
    "payment_method": "credit_card",
    "notes": "Rush delivery requested"
  }'
```

### List Orders with Filtering

```bash
# Get all orders
curl -H "X-API-Key: your-api-key-here" https://your-api-gateway-url/orders

# Get orders with pagination
curl -H "X-API-Key: your-api-key-here" "https://your-api-gateway-url/orders?page=1&page_size=10"

# Filter by status
curl -H "X-API-Key: your-api-key-here" "https://your-api-gateway-url/orders?status=pending"

# Filter by customer
curl -H "X-API-Key: your-api-key-here" "https://your-api-gateway-url/orders?customer_id=CUST001"

# Filter by date range
curl -H "X-API-Key: your-api-key-here" "https://your-api-gateway-url/orders?from_date=2024-01-01T00:00:00Z&to_date=2024-12-31T23:59:59Z"
```

### Update Order Status

```bash
curl -X PATCH https://your-api-gateway-url/orders/{order_id}/status \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{"status": "shipped"}'
```

## Monitoring and Observability

The API includes comprehensive observability features:

### Logging
- Structured JSON logging with correlation IDs
- Request/response logging for debugging
- Error logging with context information

### Tracing
- AWS X-Ray distributed tracing
- Custom annotations for order IDs and status
- Performance monitoring across all operations

### Metrics
- Custom CloudWatch metrics for:
  - Order creation/updates/deletions
  - API response times
  - Error rates by type
  - Business metrics (order values, item counts)

### Monitoring Dashboards
- CloudWatch ServiceLens for integrated view
- Application Insights for automated monitoring
- Custom dashboards for business metrics

## Error Handling

All errors return a consistent format:

```json
{
  "error": "ValidationError",
  "message": "Request validation failed",
  "details": {
    "validation_errors": [...]
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

Common error types:
- `ValidationError` (400): Invalid request data
- `BadRequest` (400): Malformed request
- `NotFound` (404): Resource not found
- `InternalServerError` (500): Unexpected errors

## Testing

### Unit Tests
```bash
# Install test dependencies
pip install -r tests/requirements.txt

# Run unit tests
python -m pytest tests/unit -v
```

### Integration Tests
```bash
# Deploy the stack first, then run integration tests
AWS_SAM_STACK_NAME="your-stack-name" python -m pytest tests/integration -v
```

### Load Testing
Use tools like [Artillery](https://www.artillery.io/) or [K6](https://k6.io/) for load testing:

```bash
# Example with curl for basic testing
for i in {1..10}; do
  curl -X GET https://your-api-gateway-url/health &
done
wait
```

## Configuration

### Environment Variables
- `POWERTOOLS_SERVICE_NAME`: Service name for observability
- `POWERTOOLS_METRICS_NAMESPACE`: CloudWatch metrics namespace
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `POWERTOOLS_LOG_LEVEL`: Powertools-specific logging level

### SAM Parameters
- `Environment`: Deployment environment (dev/staging/prod)

## Security Considerations

For production deployment, consider:

1. **Authentication**: Add API Gateway authorizers
2. **Authorization**: Implement role-based access control
3. **Rate Limiting**: Configure API Gateway throttling
4. **Data Encryption**: Enable encryption at rest and in transit
5. **Input Validation**: Already implemented with Pydantic
6. **CORS**: Configure appropriate CORS policies
7. **Secrets Management**: Use AWS Secrets Manager for sensitive data

## Database Integration

The current implementation uses in-memory storage for development. For production:

1. **DynamoDB**: Recommended for serverless applications
2. **RDS**: For relational database requirements
3. **DocumentDB**: For document-based storage

Example DynamoDB integration:
```python
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('SalesOrders')

# Replace in-memory storage operations with DynamoDB calls
def store_order(order: SalesOrder):
    table.put_item(Item=order.model_dump())
```

## Performance Optimization

- **Lambda Configuration**: Adjust memory and timeout based on usage
- **Connection Pooling**: Implement for database connections
- **Caching**: Add caching layer for frequently accessed data
- **Batch Operations**: Implement batch endpoints for bulk operations

## Cleanup

To delete the deployed application:

```bash
sam delete --stack-name your-stack-name
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions or issues:
- Check the OpenAPI specification at `/openapi.json`
- Review the health check endpoint at `/health`
- Check CloudWatch logs for detailed error information
- Use AWS X-Ray for tracing request flows
