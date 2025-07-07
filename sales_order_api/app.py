"""
Sales Order API

A comprehensive RESTful API for managing sales orders with full CRUD operations,
built with AWS Lambda Powertools for observability and Pydantic for data validation.
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
from openapi_spec import get_openapi_spec

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

# In-memory storage for development (replace with database in production)
orders_storage: dict[str, SalesOrder] = {}


def generate_order_id() -> str:
    """Generate a unique order ID."""
    return str(uuid.uuid4())


def order_to_response(order: SalesOrder) -> SalesOrderResponse:
    """Convert SalesOrder to SalesOrderResponse."""
    # Calculate computed fields manually using correct property names
    subtotal_amount = sum(item.subtotal for item in order.items)
    discount_amount = sum(item.discount_amount for item in order.items)
    tax_amount = sum(item.tax_amount for item in order.items)
    total_amount = sum(item.total_amount for item in order.items)
    item_count = sum(item.quantity for item in order.items)
    
    return SalesOrderResponse(
        order_id=order.order_id,
        order_number=order.order_number,
        customer=order.customer,
        items=order.items,
        status=order.status,
        payment_method=order.payment_method,
        currency=order.currency,
        subtotal_amount=subtotal_amount,
        tax_amount=tax_amount,
        discount_amount=discount_amount,
        total_amount=total_amount,
        item_count=item_count,
        created_at=order.created_at,
        updated_at=order.updated_at,
        requested_delivery_date=order.requested_delivery_date,
        notes=order.notes
    )


# Health check endpoint (no authentication required)
@app.get("/health")
@tracer.capture_method
def health_check():
    """
    Health check endpoint.
    
    Returns the current health status of the API service.
    """
    return {
        "status": "healthy",
        "service": "SalesOrderAPI",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
        "orders_count": len(orders_storage)
    }


# OpenAPI specification endpoint (no authentication required)
@app.get("/openapi.json")
@tracer.capture_method
def get_openapi():
    """
    Get OpenAPI 3.0 specification.
    
    Returns the complete OpenAPI specification for this API.
    """
    return get_openapi_spec()


# Order CRUD operations (require authentication)
@app.post("/orders")
@tracer.capture_method
def create_order(order_data: SalesOrderCreate) -> SalesOrderResponse:
    """
    Create a new sales order.
    
    Creates a new sales order with the provided customer and item information.
    The order is assigned a unique ID and initial status of 'draft'.
    """
    try:
        # Create new order
        order = SalesOrder(
            order_id=generate_order_id(),
            customer=order_data.customer,
            items=order_data.items,
            payment_method=order_data.payment_method,
            currency=order_data.currency,
            requested_delivery_date=order_data.requested_delivery_date,
            notes=order_data.notes,
            order_number=order_data.order_number
        )
        
        # Store order
        orders_storage[order.order_id] = order
        
        # Add metrics
        metrics.add_metric(name="OrderCreated", unit=MetricUnit.Count, value=1)
        metrics.add_metric(name="OrderValue", unit=MetricUnit.Count, value=float(order.total_amount))
        
        # Add tracing annotations
        tracer.put_annotation(key="OrderId", value=order.order_id)
        tracer.put_annotation(key="CustomerId", value=order.customer.customer_id)
        tracer.put_annotation(key="OrderStatus", value=order.status.value)
        
        logger.info(
            "Order created successfully",
            extra={
                "order_id": order.order_id,
                "customer_id": order.customer.customer_id,
                "total_amount": float(order.total_amount),
                "item_count": order.item_count
            }
        )
        
        return order_to_response(order), 201
        
    except Exception as e:
        logger.error("Order creation failed", extra={"error": str(e)})
        metrics.add_metric(name="OrderCreationError", unit=MetricUnit.Count, value=1)
        raise InternalServerError(f"Failed to create order: {str(e)}")


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
        # Start with all orders
        filtered_orders = list(orders_storage.values())
        
        # Apply filters
        if status:
            filtered_orders = [order for order in filtered_orders if order.status.value == status]
        
        if customer_id:
            filtered_orders = [order for order in filtered_orders if order.customer.customer_id == customer_id]
        
        if from_date:
            from_dt = datetime.fromisoformat(from_date.replace('Z', '+00:00'))
            filtered_orders = [order for order in filtered_orders if order.created_at >= from_dt]
        
        if to_date:
            to_dt = datetime.fromisoformat(to_date.replace('Z', '+00:00'))
            filtered_orders = [order for order in filtered_orders if order.created_at <= to_dt]
        
        # Calculate pagination
        total_count = len(filtered_orders)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_orders = filtered_orders[start_idx:end_idx]
        
        # Convert to response format
        order_responses = [order_to_response(order) for order in paginated_orders]
        
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
            has_next=end_idx < total_count,
            has_previous=page > 1
        )
        
    except Exception as e:
        logger.error("Order listing failed", extra={"error": str(e)})
        metrics.add_metric(name="OrderListingError", unit=MetricUnit.Count, value=1)
        raise InternalServerError(f"Failed to list orders: {str(e)}")


@app.get("/orders/<order_id>")
@tracer.capture_method
def get_order(order_id: str) -> SalesOrderResponse:
    """
    Get a specific sales order by ID.
    
    Returns the complete order information including customer details,
    items, pricing, and current status.
    """
    try:
        if order_id not in orders_storage:
            raise NotFoundError(f"Order {order_id} not found")
        
        order = orders_storage[order_id]
        
        # Add tracing annotations
        tracer.put_annotation(key="OrderId", value=order_id)
        tracer.put_annotation(key="OrderStatus", value=order.status.value)
        
        # Add metrics
        metrics.add_metric(name="OrderRetrieved", unit=MetricUnit.Count, value=1)
        
        logger.info(
            "Order retrieved successfully",
            extra={
                "order_id": order_id,
                "customer_id": order.customer.customer_id,
                "status": order.status.value
            }
        )
        
        return order_to_response(order)
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error("Order retrieval failed", extra={"error": str(e), "order_id": order_id})
        metrics.add_metric(name="OrderRetrievalError", unit=MetricUnit.Count, value=1)
        raise InternalServerError(f"Failed to retrieve order: {str(e)}")


@app.put("/orders/<order_id>")
@tracer.capture_method
def update_order(order_id: str, order_data: SalesOrderCreate) -> SalesOrderResponse:
    """
    Update an existing sales order.
    
    Replaces the order with new data while preserving the order ID,
    creation timestamp, and updating the modification timestamp.
    """
    try:
        if order_id not in orders_storage:
            raise NotFoundError(f"Order {order_id} not found")
        
        existing_order = orders_storage[order_id]
        
        # Create updated order preserving ID and creation time
        updated_order = SalesOrder(
            order_id=order_id,
            customer=order_data.customer,
            items=order_data.items,
            payment_method=order_data.payment_method,
            currency=order_data.currency,
            requested_delivery_date=order_data.requested_delivery_date,
            notes=order_data.notes,
            order_number=order_data.order_number,
            created_at=existing_order.created_at  # Preserve original creation time
        )
        
        # Store updated order
        orders_storage[order_id] = updated_order
        
        # Add metrics
        metrics.add_metric(name="OrderUpdated", unit=MetricUnit.Count, value=1)
        
        # Add tracing annotations
        tracer.put_annotation(key="OrderId", value=order_id)
        tracer.put_annotation(key="OrderStatus", value=updated_order.status.value)
        
        logger.info(
            "Order updated successfully",
            extra={
                "order_id": order_id,
                "customer_id": updated_order.customer.customer_id,
                "total_amount": float(updated_order.total_amount)
            }
        )
        
        return order_to_response(updated_order)
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error("Order update failed", extra={"error": str(e), "order_id": order_id})
        metrics.add_metric(name="OrderUpdateError", unit=MetricUnit.Count, value=1)
        raise InternalServerError(f"Failed to update order: {str(e)}")


@app.delete("/orders/<order_id>")
@tracer.capture_method
def delete_order(order_id: str):
    """
    Delete a sales order.
    
    Permanently removes the order from the system.
    This action cannot be undone.
    """
    try:
        if order_id not in orders_storage:
            raise NotFoundError(f"Order {order_id} not found")
        
        order = orders_storage[order_id]
        del orders_storage[order_id]
        
        # Add metrics
        metrics.add_metric(name="OrderDeleted", unit=MetricUnit.Count, value=1)
        
        # Add tracing annotations
        tracer.put_annotation(key="OrderId", value=order_id)
        tracer.put_annotation(key="OrderStatus", value=order.status.value)
        
        logger.info(
            "Order deleted successfully",
            extra={
                "order_id": order_id,
                "customer_id": order.customer.customer_id
            }
        )
        
        return {"message": f"Order {order_id} deleted successfully"}
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error("Order deletion failed", extra={"error": str(e), "order_id": order_id})
        metrics.add_metric(name="OrderDeletionError", unit=MetricUnit.Count, value=1)
        raise InternalServerError(f"Failed to delete order: {str(e)}")


# Order status operations
@app.get("/orders/<order_id>/status")
@tracer.capture_method
def get_order_status(order_id: str):
    """
    Get the current status of a sales order.
    
    Returns just the status information for quick status checks.
    """
    try:
        if order_id not in orders_storage:
            raise NotFoundError(f"Order {order_id} not found")
        
        order = orders_storage[order_id]
        
        # Add tracing annotations
        tracer.put_annotation(key="OrderId", value=order_id)
        tracer.put_annotation(key="OrderStatus", value=order.status.value)
        
        # Add metrics
        metrics.add_metric(name="OrderStatusRetrieved", unit=MetricUnit.Count, value=1)
        
        return {
            "order_id": order_id,
            "status": order.status.value,
            "updated_at": order.updated_at.isoformat()
        }
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error("Order status retrieval failed", extra={"error": str(e), "order_id": order_id})
        metrics.add_metric(name="OrderStatusRetrievalError", unit=MetricUnit.Count, value=1)
        raise InternalServerError(f"Failed to retrieve order status: {str(e)}")


@app.patch("/orders/<order_id>/status")
@tracer.capture_method
def update_order_status(order_id: str, status_update: OrderStatusUpdate):
    """
    Update the status of a sales order.
    
    Updates only the order status while preserving all other order data.
    The updated timestamp is automatically set to the current time.
    """
    try:
        if order_id not in orders_storage:
            raise NotFoundError(f"Order {order_id} not found")
        
        order = orders_storage[order_id]
        previous_status = order.status
        
        # Update status and timestamp
        order.status = status_update.status
        order.updated_at = datetime.now(timezone.utc)
        
        # Add metrics
        metrics.add_metric(name="OrderStatusUpdated", unit=MetricUnit.Count, value=1)
        
        # Add tracing annotations
        tracer.put_annotation(key="OrderId", value=order_id)
        tracer.put_annotation(key="OrderStatus", value=order.status.value)
        tracer.put_annotation(key="PreviousStatus", value=previous_status.value)
        
        logger.info(
            "Order status updated successfully",
            extra={
                "order_id": order_id,
                "previous_status": previous_status.value,
                "new_status": order.status.value,
                "customer_id": order.customer.customer_id
            }
        )
        
        return {
            "order_id": order_id,
            "status": order.status.value,
            "previous_status": previous_status.value,
            "updated_at": order.updated_at.isoformat()
        }
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error("Order status update failed", extra={"error": str(e), "order_id": order_id})
        metrics.add_metric(name="OrderStatusUpdateError", unit=MetricUnit.Count, value=1)
        raise InternalServerError(f"Failed to update order status: {str(e)}")


# Lambda handler
@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@tracer.capture_lambda_handler
@metrics.log_metrics
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    """
    AWS Lambda handler function.
    
    Processes API Gateway events and routes them to appropriate handlers.
    """
    return app.resolve(event, context)
