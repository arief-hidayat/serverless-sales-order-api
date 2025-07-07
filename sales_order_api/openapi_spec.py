"""
OpenAPI 3.0 specification for the Sales Order API.

This module generates the complete OpenAPI specification that describes
all endpoints, request/response models, and authentication requirements.
"""

def get_openapi_spec():
    """
    Generate OpenAPI 3.0 specification for the Sales Order API.
    
    Returns a complete OpenAPI specification that can be used by
    Swagger UI, Postman, and other API documentation tools.
    """
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "Sales Order API",
            "version": "1.0.0",
            "description": "A comprehensive RESTful API for managing sales orders with full CRUD operations, built with AWS Lambda Powertools for observability and Pydantic for data validation. This API is specifically designed to be AI-agent friendly with extensive documentation, validation, and error handling.",
            "contact": {
                "name": "Sales Order API Support",
                "email": "support@example.com"
            },
            "license": {
                "name": "MIT",
                "url": "https://opensource.org/licenses/MIT"
            }
        },
        "servers": [
            {
                "url": "/",
                "description": "Current server"
            }
        ],
        "components": {
            "securitySchemes": {
                "ApiKeyAuth": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-API-Key",
                    "description": "API key for accessing protected endpoints. Click the 'Authorize' button below to enter your API key. Get your API key from the CloudFormation stack outputs after deployment."
                }
            },
            "schemas": {
                "Address": {
                    "type": "object",
                    "required": ["street", "city", "state", "postal_code", "country"],
                    "properties": {
                        "street": {"type": "string", "minLength": 1, "maxLength": 200},
                        "city": {"type": "string", "minLength": 1, "maxLength": 100},
                        "state": {"type": "string", "minLength": 1, "maxLength": 100},
                        "postal_code": {"type": "string", "minLength": 1, "maxLength": 20},
                        "country": {"type": "string", "minLength": 1, "maxLength": 100}
                    }
                },
                "Customer": {
                    "type": "object",
                    "required": ["customer_id", "first_name", "last_name", "email", "billing_address"],
                    "properties": {
                        "customer_id": {"type": "string", "minLength": 1, "maxLength": 50},
                        "first_name": {"type": "string", "minLength": 1, "maxLength": 100},
                        "last_name": {"type": "string", "minLength": 1, "maxLength": 100},
                        "email": {"type": "string", "format": "email"},
                        "phone": {"type": "string", "maxLength": 20},
                        "billing_address": {"$ref": "#/components/schemas/Address"},
                        "shipping_address": {"$ref": "#/components/schemas/Address"}
                    }
                },
                "OrderItem": {
                    "type": "object",
                    "required": ["item_id", "product_name", "quantity", "unit_price"],
                    "properties": {
                        "item_id": {"type": "string", "minLength": 1, "maxLength": 50},
                        "product_name": {"type": "string", "minLength": 1, "maxLength": 200},
                        "sku": {"type": "string", "maxLength": 50},
                        "quantity": {"type": "integer", "minimum": 1, "maximum": 10000},
                        "unit_price": {"type": "number", "minimum": 0, "multipleOf": 0.01},
                        "discount_percent": {"type": "number", "minimum": 0, "maximum": 100, "multipleOf": 0.01},
                        "tax_percent": {"type": "number", "minimum": 0, "maximum": 100, "multipleOf": 0.01}
                    }
                },
                "SalesOrderCreate": {
                    "type": "object",
                    "required": ["customer", "items", "payment_method"],
                    "properties": {
                        "customer": {"$ref": "#/components/schemas/Customer"},
                        "items": {
                            "type": "array",
                            "minItems": 1,
                            "maxItems": 100,
                            "items": {"$ref": "#/components/schemas/OrderItem"}
                        },
                        "payment_method": {
                            "type": "string",
                            "enum": ["credit_card", "debit_card", "bank_transfer", "cash", "check", "digital_wallet"]
                        },
                        "currency": {"type": "string", "pattern": "^[A-Z]{3}$", "default": "USD"},
                        "requested_delivery_date": {"type": "string", "format": "date-time"},
                        "notes": {"type": "string", "maxLength": 1000},
                        "order_number": {"type": "string", "maxLength": 50}
                    }
                },
                "SalesOrderResponse": {
                    "type": "object",
                    "properties": {
                        "order_id": {"type": "string"},
                        "order_number": {"type": "string"},
                        "customer": {"$ref": "#/components/schemas/Customer"},
                        "items": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/OrderItem"}
                        },
                        "status": {
                            "type": "string",
                            "enum": ["draft", "pending", "confirmed", "shipped", "delivered", "cancelled", "returned"]
                        },
                        "payment_method": {"type": "string"},
                        "currency": {"type": "string"},
                        "subtotal_amount": {"type": "string"},
                        "discount_amount": {"type": "string"},
                        "tax_amount": {"type": "string"},
                        "total_amount": {"type": "string"},
                        "item_count": {"type": "integer"},
                        "created_at": {"type": "string", "format": "date-time"},
                        "updated_at": {"type": "string", "format": "date-time"},
                        "requested_delivery_date": {"type": "string", "format": "date-time"},
                        "notes": {"type": "string"}
                    }
                },
                "OrderStatusUpdate": {
                    "type": "object",
                    "required": ["status"],
                    "properties": {
                        "status": {
                            "type": "string",
                            "enum": ["draft", "pending", "confirmed", "shipped", "delivered", "cancelled", "returned"]
                        }
                    }
                },
                "HealthResponse": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "service": {"type": "string"},
                        "timestamp": {"type": "string"},
                        "version": {"type": "string"},
                        "orders_count": {"type": "integer"}
                    }
                },
                "ErrorResponse": {
                    "type": "object",
                    "properties": {
                        "statusCode": {"type": "integer"},
                        "message": {"type": "string"}
                    }
                }
            }
        },
        "security": [
            {"ApiKeyAuth": []}
        ],
        "paths": {
            "/health": {
                "get": {
                    "summary": "Health Check",
                    "description": "Returns the current health status of the API service",
                    "operationId": "healthCheck",
                    "security": [],  # Public endpoint - no authentication required
                    "responses": {
                        "200": {
                            "description": "Service is healthy",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/HealthResponse"}
                                }
                            }
                        }
                    }
                }
            },
            "/openapi.json": {
                "get": {
                    "summary": "OpenAPI Specification",
                    "description": "Returns the complete OpenAPI 3.0 specification for this API",
                    "operationId": "getOpenAPISpec",
                    "security": [],  # Public endpoint - no authentication required
                    "responses": {
                        "200": {
                            "description": "OpenAPI specification",
                            "content": {
                                "application/json": {
                                    "schema": {"type": "object"}
                                }
                            }
                        }
                    }
                }
            },
            "/orders": {
                "post": {
                    "summary": "Create Order",
                    "description": "Create a new sales order with customer and item information",
                    "operationId": "createOrder",
                    "security": [{"ApiKeyAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/SalesOrderCreate"},
                                "example": {
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
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "Order created successfully",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/SalesOrderResponse"}
                                }
                            }
                        },
                        "400": {
                            "description": "Invalid request data",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            }
                        },
                        "401": {
                            "description": "Missing or invalid API key",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            }
                        }
                    }
                },
                "get": {
                    "summary": "List Orders",
                    "description": "List sales orders with optional filtering and pagination",
                    "operationId": "listOrders",
                    "security": [{"ApiKeyAuth": []}],
                    "parameters": [
                        {
                            "name": "page",
                            "in": "query",
                            "description": "Page number for pagination",
                            "schema": {"type": "integer", "minimum": 1, "default": 1}
                        },
                        {
                            "name": "page_size",
                            "in": "query",
                            "description": "Number of items per page",
                            "schema": {"type": "integer", "minimum": 1, "maximum": 100, "default": 10}
                        },
                        {
                            "name": "status",
                            "in": "query",
                            "description": "Filter by order status",
                            "schema": {
                                "type": "string",
                                "enum": ["draft", "pending", "confirmed", "shipped", "delivered", "cancelled", "returned"]
                            }
                        },
                        {
                            "name": "customer_id",
                            "in": "query",
                            "description": "Filter by customer ID",
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "List of orders",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "orders": {
                                                "type": "array",
                                                "items": {"$ref": "#/components/schemas/SalesOrderResponse"}
                                            },
                                            "total_count": {"type": "integer"},
                                            "page": {"type": "integer"},
                                            "page_size": {"type": "integer"},
                                            "has_next": {"type": "boolean"},
                                            "has_previous": {"type": "boolean"}
                                        }
                                    }
                                }
                            }
                        },
                        "401": {
                            "description": "Missing or invalid API key",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            }
                        }
                    }
                }
            },
            "/orders/{order_id}": {
                "get": {
                    "summary": "Get Order",
                    "description": "Get a specific sales order by ID",
                    "operationId": "getOrder",
                    "security": [{"ApiKeyAuth": []}],
                    "parameters": [
                        {
                            "name": "order_id",
                            "in": "path",
                            "required": True,
                            "description": "Unique order identifier",
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Order details",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/SalesOrderResponse"}
                                }
                            }
                        },
                        "404": {
                            "description": "Order not found",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            }
                        },
                        "401": {
                            "description": "Missing or invalid API key",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            }
                        }
                    }
                },
                "put": {
                    "summary": "Update Order",
                    "description": "Update an existing sales order",
                    "operationId": "updateOrder",
                    "security": [{"ApiKeyAuth": []}],
                    "parameters": [
                        {
                            "name": "order_id",
                            "in": "path",
                            "required": True,
                            "description": "Unique order identifier",
                            "schema": {"type": "string"}
                        }
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/SalesOrderCreate"}
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Order updated successfully",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/SalesOrderResponse"}
                                }
                            }
                        },
                        "404": {
                            "description": "Order not found",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            }
                        },
                        "401": {
                            "description": "Missing or invalid API key",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            }
                        }
                    }
                },
                "delete": {
                    "summary": "Delete Order",
                    "description": "Delete a sales order",
                    "operationId": "deleteOrder",
                    "security": [{"ApiKeyAuth": []}],
                    "parameters": [
                        {
                            "name": "order_id",
                            "in": "path",
                            "required": True,
                            "description": "Unique order identifier",
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Order deleted successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "message": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        },
                        "404": {
                            "description": "Order not found",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            }
                        },
                        "401": {
                            "description": "Missing or invalid API key",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            }
                        }
                    }
                }
            },
            "/orders/{order_id}/status": {
                "get": {
                    "summary": "Get Order Status",
                    "description": "Get the current status of a sales order",
                    "operationId": "getOrderStatus",
                    "security": [{"ApiKeyAuth": []}],
                    "parameters": [
                        {
                            "name": "order_id",
                            "in": "path",
                            "required": True,
                            "description": "Unique order identifier",
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Order status",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "order_id": {"type": "string"},
                                            "status": {"type": "string"},
                                            "updated_at": {"type": "string", "format": "date-time"}
                                        }
                                    }
                                }
                            }
                        },
                        "404": {
                            "description": "Order not found",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            }
                        },
                        "401": {
                            "description": "Missing or invalid API key",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            }
                        }
                    }
                },
                "patch": {
                    "summary": "Update Order Status",
                    "description": "Update the status of a sales order",
                    "operationId": "updateOrderStatus",
                    "security": [{"ApiKeyAuth": []}],
                    "parameters": [
                        {
                            "name": "order_id",
                            "in": "path",
                            "required": True,
                            "description": "Unique order identifier",
                            "schema": {"type": "string"}
                        }
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/OrderStatusUpdate"},
                                "example": {
                                    "status": "confirmed"
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Order status updated successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "order_id": {"type": "string"},
                                            "status": {"type": "string"},
                                            "previous_status": {"type": "string"},
                                            "updated_at": {"type": "string", "format": "date-time"}
                                        }
                                    }
                                }
                            }
                        },
                        "404": {
                            "description": "Order not found",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            }
                        },
                        "401": {
                            "description": "Missing or invalid API key",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            }
                        }
                    }
                }
            }
        }
    }
