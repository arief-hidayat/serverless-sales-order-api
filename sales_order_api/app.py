"""
Sales Order API

A comprehensive RESTful API for managing sales orders with full CRUD operations,
built with AWS Lambda Powertools for observability and DynamoDB for persistent storage.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver, Response
from aws_lambda_powertools.event_handler.exceptions import (
    BadRequestError,
    InternalServerError,
    NotFoundError,
)
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.utilities.typing import LambdaContext
from pydantic import ValidationError

from models import (
    OrderStatusUpdate,
    SalesOrder,
    SalesOrderCreate,
    SalesOrderResponse,
    SalesOrdersListResponse,
)
from storage import storage

# Initialize Powertools
tracer = Tracer()
logger = Logger()
metrics = Metrics()

# Initialize API Gateway resolver with data validation enabled
app = APIGatewayRestResolver(
    enable_validation=True,
    debug=True,
    strip_prefixes=["/Prod", "/Stage", "/Dev"]
)

# Configure OpenAPI metadata to use our custom specification
app.configure_openapi(
    title="Sales Order API",
    version="1.0.0",
    description="A comprehensive RESTful API for managing sales orders with full CRUD operations. This API is specifically designed to be AI-agent friendly with extensive documentation, validation, and error handling.",
    openapi_version="3.0.3",
    security_schemes={
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API key for accessing protected endpoints. Click the 'Authorize' button below to enter your API key. Get your API key from the CloudFormation stack outputs after deployment."
        }
    },
    security=[{"ApiKeyAuth": []}]
)

# Enable Swagger UI with embedded assets and API key support
app.enable_swagger(
    path="/swagger",
    persist_authorization=True,  # Keep API key after browser refresh
    compress=True  # Compress the embedded assets for better performance
)


def order_to_response(order: SalesOrder) -> SalesOrderResponse:
    """Convert SalesOrder to SalesOrderResponse with calculated fields."""
    return SalesOrderResponse(
        order_id=order.order_id,
        order_number=order.order_number,
        customer=order.customer,
        items=order.items,
        status=order.status,
        payment_method=order.payment_method,
        currency=order.currency,
        subtotal_amount=order.subtotal,
        discount_amount=order.total_discount,
        tax_amount=order.total_tax,
        total_amount=order.total_amount,
        item_count=order.item_count,
        created_at=order.created_at,
        updated_at=order.updated_at,
        requested_delivery_date=order.requested_delivery_date,
        notes=order.notes,
    )


# Health check endpoint (no authentication required)
@app.get("/health")
@tracer.capture_method
def health_check():
    """
    Health check endpoint.
    
    Returns the current health status of the API service.
    """
    try:
        orders_count = storage.count_orders()
    except Exception as e:
        logger.error(f"Failed to get orders count: {e}")
        orders_count = "unavailable"
    
    return {
        "status": "healthy",
        "service": "SalesOrderAPI",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
        "orders_count": orders_count
    }


@app.post("/orders")
@tracer.capture_method
def create_order(order_data: SalesOrderCreate) -> SalesOrderResponse:
    """
    Create a new sales order.
    
    Creates a new order with the provided customer and item information.
    Returns the created order with calculated totals and assigned ID.
    """
    try:
        # Create SalesOrder from input data
        order = SalesOrder(
            customer=order_data.customer,
            items=order_data.items,
            payment_method=order_data.payment_method,
            order_number=order_data.order_number,
            requested_delivery_date=order_data.requested_delivery_date,
            notes=order_data.notes,
        )
        
        # Store order in DynamoDB
        storage.create_order(order)
        
        # Add metrics
        metrics.add_metric(name="OrderCreated", unit=MetricUnit.Count, value=1)
        metrics.add_metric(name="OrderValue", unit=MetricUnit.Count, value=float(order.total_amount))
        
        # Add tracing annotations
        tracer.put_annotation(key="OrderId", value=order.order_id)
        tracer.put_annotation(key="CustomerId", value=order.customer.customer_id)
        tracer.put_annotation(key="OrderValue", value=str(order.total_amount))
        
        logger.info(
            "Order created successfully",
            extra={
                "order_id": order.order_id,
                "customer_id": order.customer.customer_id,
                "total_amount": str(order.total_amount),
                "item_count": order.item_count
            }
        )
        
        # Return with 201 status code
        return Response(
            status_code=201,
            content_type="application/json",
            body=order_to_response(order).model_dump()
        )
        
    except ValidationError as e:
        logger.error(f"Validation error creating order: {e}")
        metrics.add_metric(name="OrderValidationError", unit=MetricUnit.Count, value=1)
        raise BadRequestError(f"Invalid order data: {e}")
    except Exception as e:
        logger.error(f"Failed to create order: {e}")
        metrics.add_metric(name="OrderCreationError", unit=MetricUnit.Count, value=1)
        raise InternalServerError(f"Failed to create order: {str(e)}")


# List sales orders with filtering and pagination
@app.get("/orders")
@tracer.capture_method
def list_orders(
    page: int = 1,
    page_size: int = 10,
    status: Optional[str] = None,
    customer_id: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None
) -> SalesOrdersListResponse:
    """
    List sales orders with optional filtering and pagination.
    
    Supports filtering by status, customer ID, and date range.
    Results are paginated with configurable page size.
    """
    try:
        # Parse date filters if provided
        from_dt = None
        to_dt = None
        if from_date:
            from_dt = datetime.fromisoformat(from_date.replace('Z', '+00:00'))
        if to_date:
            to_dt = datetime.fromisoformat(to_date.replace('Z', '+00:00'))
        
        # Get orders from DynamoDB with filtering
        result = storage.list_orders(
            status=status,
            customer_id=customer_id,
            from_date=from_dt,
            to_date=to_dt,
            page_size=page_size
        )
        
        orders = result['orders']
        
        # Apply pagination (DynamoDB handles this, but we simulate for compatibility)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_orders = orders[start_idx:end_idx] if len(orders) > start_idx else []
        
        # Convert to response format
        order_responses = [order_to_response(order) for order in paginated_orders]
        
        # Calculate pagination info
        total_count = len(orders)  # This is approximate for DynamoDB
        has_next = len(orders) == page_size  # Simplified check
        has_previous = page > 1
        
        # Add metrics
        metrics.add_metric(name="OrdersListed", unit=MetricUnit.Count, value=len(order_responses))
        
        logger.info(
            "Orders listed successfully",
            extra={
                "total_count": total_count,
                "page": page,
                "page_size": page_size,
                "returned_count": len(order_responses)
            }
        )
        
        return SalesOrdersListResponse(
            orders=order_responses,
            total_count=total_count,
            page=page,
            page_size=page_size,
            has_next=has_next,
            has_previous=has_previous
        )
        
    except Exception as e:
        logger.error(f"Failed to list orders: {e}")
        metrics.add_metric(name="OrderListError", unit=MetricUnit.Count, value=1)
        raise InternalServerError(f"Failed to list orders: {str(e)}")


# Get a specific sales order
@app.get("/orders/<order_id>")
@tracer.capture_method
def get_order(order_id: str) -> SalesOrderResponse:
    """
    Get a specific sales order by ID.
    
    Returns the complete order information including customer details,
    items, pricing, and current status.
    """
    try:
        order = storage.get_order(order_id)
        if not order:
            raise NotFoundError(f"Order {order_id} not found")
        
        # Add tracing annotations
        tracer.put_annotation(key="OrderId", value=order_id)
        tracer.put_annotation(key="OrderStatus", value=order.status.value)
        
        # Add metrics
        metrics.add_metric(name="OrderRetrieved", unit=MetricUnit.Count, value=1)
        
        logger.info(f"Order retrieved successfully: {order_id}")
        
        return order_to_response(order)
        
    except NotFoundError:
        metrics.add_metric(name="OrderNotFound", unit=MetricUnit.Count, value=1)
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve order {order_id}: {e}")
        metrics.add_metric(name="OrderRetrievalError", unit=MetricUnit.Count, value=1)
        raise InternalServerError(f"Failed to retrieve order: {str(e)}")


# Update a sales order
@app.put("/orders/<order_id>")
@tracer.capture_method
def update_order(order_id: str, order_data: SalesOrderCreate) -> SalesOrderResponse:
    """
    Update an existing sales order.
    
    Updates the order with new information while preserving the original
    order ID and creation timestamp.
    """
    try:
        existing_order = storage.get_order(order_id)
        if not existing_order:
            raise NotFoundError(f"Order {order_id} not found")
        
        # Create updated order preserving ID and creation time
        updated_order = SalesOrder(
            order_id=existing_order.order_id,
            customer=order_data.customer,
            items=order_data.items,
            payment_method=order_data.payment_method,
            order_number=order_data.order_number,
            requested_delivery_date=order_data.requested_delivery_date,
            notes=order_data.notes,
            created_at=existing_order.created_at,  # Preserve original creation time
        )
        
        # Store updated order
        storage.update_order(updated_order)
        
        # Add metrics
        metrics.add_metric(name="OrderUpdated", unit=MetricUnit.Count, value=1)
        
        # Add tracing annotations
        tracer.put_annotation(key="OrderId", value=order_id)
        tracer.put_annotation(key="OrderStatus", value=updated_order.status.value)
        
        logger.info(f"Order updated successfully: {order_id}")
        
        return order_to_response(updated_order)
        
    except NotFoundError:
        metrics.add_metric(name="OrderUpdateNotFound", unit=MetricUnit.Count, value=1)
        raise
    except ValidationError as e:
        logger.error(f"Validation error updating order {order_id}: {e}")
        metrics.add_metric(name="OrderUpdateValidationError", unit=MetricUnit.Count, value=1)
        raise BadRequestError(f"Invalid order data: {e}")
    except Exception as e:
        logger.error(f"Failed to update order {order_id}: {e}")
        metrics.add_metric(name="OrderUpdateError", unit=MetricUnit.Count, value=1)
        raise InternalServerError(f"Failed to update order: {str(e)}")


# Delete a sales order
@app.delete("/orders/<order_id>")
@tracer.capture_method
def delete_order(order_id: str) -> dict:
    """
    Delete a sales order.
    
    Permanently removes the order from the system.
    Returns confirmation of deletion.
    """
    try:
        deleted = storage.delete_order(order_id)
        if not deleted:
            raise NotFoundError(f"Order {order_id} not found")
        
        # Add metrics
        metrics.add_metric(name="OrderDeleted", unit=MetricUnit.Count, value=1)
        
        # Add tracing annotations
        tracer.put_annotation(key="OrderId", value=order_id)
        
        logger.info(f"Order deleted successfully: {order_id}")
        
        return {
            "message": f"Order {order_id} deleted successfully",
            "order_id": order_id,
            "deleted_at": datetime.now(timezone.utc).isoformat()
        }
        
    except NotFoundError:
        metrics.add_metric(name="OrderDeleteNotFound", unit=MetricUnit.Count, value=1)
        raise
    except Exception as e:
        logger.error(f"Failed to delete order {order_id}: {e}")
        metrics.add_metric(name="OrderDeleteError", unit=MetricUnit.Count, value=1)
        raise InternalServerError(f"Failed to delete order: {str(e)}")


# Get order status
@app.get("/orders/<order_id>/status")
@tracer.capture_method
def get_order_status(order_id: str) -> dict:
    """
    Get the current status of a sales order.
    
    Returns just the status information for quick status checks.
    """
    try:
        order = storage.get_order(order_id)
        if not order:
            raise NotFoundError(f"Order {order_id} not found")
        
        # Add tracing annotations
        tracer.put_annotation(key="OrderId", value=order_id)
        tracer.put_annotation(key="OrderStatus", value=order.status.value)
        
        logger.info(f"Order status retrieved: {order_id} - {order.status.value}")
        
        return {
            "order_id": order_id,
            "status": order.status.value,
            "updated_at": order.updated_at.isoformat()
        }
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Failed to get order status {order_id}: {e}")
        raise InternalServerError(f"Failed to get order status: {str(e)}")


# Update order status only
@app.patch("/orders/<order_id>/status")
@tracer.capture_method
def update_order_status(order_id: str, status_update: OrderStatusUpdate) -> dict:
    """
    Update only the status of a sales order.
    
    Allows for quick status updates without modifying other order details.
    Useful for order fulfillment workflows.
    """
    try:
        order = storage.get_order(order_id)
        if not order:
            raise NotFoundError(f"Order {order_id} not found")
        
        previous_status = order.status
        
        # Update only the status and timestamp
        order.status = status_update.status
        order.updated_at = datetime.now(timezone.utc)
        
        # Store updated order
        storage.update_order(order)
        
        # Add metrics
        metrics.add_metric(name="OrderStatusUpdated", unit=MetricUnit.Count, value=1)
        
        # Add tracing annotations
        tracer.put_annotation(key="OrderId", value=order_id)
        tracer.put_annotation(key="PreviousStatus", value=previous_status.value)
        tracer.put_annotation(key="NewStatus", value=order.status.value)
        
        logger.info(
            f"Order status updated: {order_id}",
            extra={
                "order_id": order_id,
                "previous_status": previous_status.value,
                "new_status": order.status.value
            }
        )
        
        return {
            "order_id": order_id,
            "previous_status": previous_status.value,
            "new_status": order.status.value,
            "updated_at": order.updated_at.isoformat()
        }
        
    except NotFoundError:
        raise
    except ValidationError as e:
        logger.error(f"Validation error updating order status {order_id}: {e}")
        raise BadRequestError(f"Invalid status data: {e}")
    except Exception as e:
        logger.error(f"Failed to update order status {order_id}: {e}")
        raise InternalServerError(f"Failed to update order status: {str(e)}")


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    """
    AWS Lambda handler function.
    
    Processes API Gateway events and routes them to appropriate handlers.
    Includes comprehensive logging, tracing, and metrics collection.
    """
    try:
        return app.resolve(event, context)
    except Exception as e:
        logger.error(f"Unhandled error in lambda handler: {e}")
        metrics.add_metric(name="UnhandledError", unit=MetricUnit.Count, value=1)
        raise
