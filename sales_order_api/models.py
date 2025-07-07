"""
Sales Order API Data Models

This module defines the Pydantic models for the Sales Order API.
All models include comprehensive validation and documentation for AI agents.
"""

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator, model_validator


class OrderStatus(str, Enum):
    """
    Sales order status enumeration.
    
    Values:
    - DRAFT: Order is being created but not yet submitted
    - PENDING: Order submitted and awaiting processing
    - CONFIRMED: Order confirmed and being prepared
    - SHIPPED: Order has been shipped to customer
    - DELIVERED: Order successfully delivered to customer
    - CANCELLED: Order was cancelled before fulfillment
    - RETURNED: Order was returned by customer
    """
    DRAFT = "draft"
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNED = "returned"


class PaymentMethod(str, Enum):
    """
    Payment method enumeration.
    
    Values:
    - CREDIT_CARD: Payment via credit card
    - DEBIT_CARD: Payment via debit card
    - BANK_TRANSFER: Direct bank transfer
    - PAYPAL: PayPal payment
    - CASH_ON_DELIVERY: Cash payment upon delivery
    """
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_TRANSFER = "bank_transfer"
    PAYPAL = "paypal"
    CASH_ON_DELIVERY = "cash_on_delivery"


class Address(BaseModel):
    """
    Customer address information.
    
    This model represents a complete address for shipping or billing purposes.
    All fields are validated for proper format and completeness.
    """
    street: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Street address including house number and street name"
    )
    city: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="City name"
    )
    state: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="State or province name"
    )
    postal_code: str = Field(
        ...,
        min_length=3,
        max_length=20,
        description="Postal or ZIP code"
    )
    country: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Country name or ISO country code"
    )

    @field_validator('postal_code')
    @classmethod
    def validate_postal_code(cls, v: str) -> str:
        """Validate postal code format."""
        if not v.replace('-', '').replace(' ', '').isalnum():
            raise ValueError('Postal code must contain only alphanumeric characters, spaces, and hyphens')
        return v.strip()


class Customer(BaseModel):
    """
    Customer information for the sales order.
    
    Contains all necessary customer details including contact information
    and addresses for billing and shipping.
    """
    customer_id: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Unique customer identifier in the system"
    )
    first_name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Customer's first name"
    )
    last_name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Customer's last name"
    )
    email: str = Field(
        ...,
        description="Customer's email address for order notifications"
    )
    phone: Optional[str] = Field(
        None,
        min_length=10,
        max_length=20,
        description="Customer's phone number for order updates"
    )
    billing_address: Address = Field(
        ...,
        description="Customer's billing address for payment processing"
    )
    shipping_address: Optional[Address] = Field(
        None,
        description="Customer's shipping address (if different from billing)"
    )

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Basic email validation."""
        if '@' not in v or '.' not in v.split('@')[-1]:
            raise ValueError('Invalid email format')
        return v.lower().strip()


class OrderItem(BaseModel):
    """
    Individual item within a sales order.
    
    Represents a single product or service being ordered, including
    quantity, pricing, and product details.
    """
    item_id: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Unique identifier for the product or service"
    )
    product_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Name or description of the product/service"
    )
    sku: Optional[str] = Field(
        None,
        max_length=50,
        description="Stock Keeping Unit (SKU) for inventory tracking"
    )
    quantity: int = Field(
        default=1,
        gt=0,
        description="Number of units being ordered (must be positive, defaults to 1)"
    )
    unit_price: Decimal = Field(
        ...,
        gt=0,
        decimal_places=2,
        description="Price per unit in the order currency"
    )
    discount_percent: Optional[Decimal] = Field(
        default=Decimal('0.00'),
        ge=0,
        le=100,
        decimal_places=2,
        description="Discount percentage applied to this item (0-100, defaults to 0%)"
    )
    tax_percent: Optional[Decimal] = Field(
        default=Decimal('10.00'),
        ge=0,
        le=100,
        decimal_places=2,
        description="Tax percentage applied to this item (0-100, defaults to 10%)"
    )

    @property
    def subtotal(self) -> Decimal:
        """Calculate subtotal before discount and tax."""
        return self.unit_price * self.quantity

    @property
    def discount_amount(self) -> Decimal:
        """Calculate discount amount."""
        if self.discount_percent:
            return self.subtotal * (self.discount_percent / 100)
        return Decimal('0.00')

    @property
    def taxable_amount(self) -> Decimal:
        """Calculate amount subject to tax (after discount)."""
        return self.subtotal - self.discount_amount

    @property
    def tax_amount(self) -> Decimal:
        """Calculate tax amount."""
        if self.tax_percent:
            return self.taxable_amount * (self.tax_percent / 100)
        return Decimal('0.00')

    @property
    def total_amount(self) -> Decimal:
        """Calculate total amount for this item (including tax, after discount)."""
        return self.taxable_amount + self.tax_amount


class SalesOrder(BaseModel):
    """
    Complete sales order model.
    
    This is the main model representing a complete sales order with all
    customer information, items, pricing, and order management details.
    Designed to be comprehensive for AI agents to understand and process.
    """
    order_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique order identifier (UUID format)"
    )
    order_number: Optional[str] = Field(
        None,
        max_length=50,
        description="Human-readable order number for customer reference"
    )
    customer: Customer = Field(
        ...,
        description="Complete customer information including addresses"
    )
    items: List[OrderItem] = Field(
        ...,
        min_length=1,
        description="List of items being ordered (at least one required)"
    )
    status: OrderStatus = Field(
        default=OrderStatus.DRAFT,
        description="Current status of the order in the fulfillment process"
    )
    payment_method: Optional[PaymentMethod] = Field(
        default=PaymentMethod.CREDIT_CARD,
        description="Method of payment for this order (defaults to credit_card)"
    )
    currency: str = Field(
        default="USD",
        min_length=3,
        max_length=3,
        description="Three-letter currency code (ISO 4217)"
    )
    order_date: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Date and time when the order was created (UTC)"
    )
    requested_delivery_date: Optional[datetime] = Field(
        None,
        description="Customer's requested delivery date (UTC)"
    )
    notes: Optional[str] = Field(
        None,
        max_length=1000,
        description="Additional notes or special instructions for the order"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the order record was created (UTC)"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the order was last modified (UTC)"
    )

    @property
    def subtotal(self) -> Decimal:
        """Calculate order subtotal (sum of all item subtotals)."""
        return sum(item.subtotal for item in self.items)

    @property
    def total_discount(self) -> Decimal:
        """Calculate total discount amount across all items."""
        return sum(item.discount_amount for item in self.items)

    @property
    def total_tax(self) -> Decimal:
        """Calculate total tax amount across all items."""
        return sum(item.tax_amount for item in self.items)

    @property
    def total_amount(self) -> Decimal:
        """Calculate final order total (subtotal - discount + tax)."""
        return sum(item.total_amount for item in self.items)

    @property
    def item_count(self) -> int:
        """Get total number of individual items (sum of quantities)."""
        return sum(item.quantity for item in self.items)

    @model_validator(mode='after')
    def validate_delivery_date(self):
        """Ensure requested delivery date is in the future."""
        if self.requested_delivery_date:
            # Get current time in UTC with timezone info
            now_utc = datetime.now(timezone.utc)
            
            # If the requested date is timezone-naive, assume it's UTC
            if self.requested_delivery_date.tzinfo is None:
                requested_date = self.requested_delivery_date.replace(tzinfo=timezone.utc)
            else:
                requested_date = self.requested_delivery_date
            
            if requested_date <= now_utc:
                raise ValueError('Requested delivery date must be in the future')
        return self

    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Validate currency code format."""
        return v.upper().strip()


class SalesOrderCreate(BaseModel):
    """
    Model for creating a new sales order.
    
    This model is used for API requests to create new orders.
    It excludes auto-generated fields like order_id and timestamps.
    """
    order_number: Optional[str] = Field(
        None,
        max_length=50,
        description="Optional human-readable order number"
    )
    customer: Customer = Field(
        ...,
        description="Complete customer information"
    )
    items: List[OrderItem] = Field(
        ...,
        min_length=1,
        description="List of items to order (minimum 1 required)"
    )
    payment_method: Optional[PaymentMethod] = Field(
        default=PaymentMethod.CREDIT_CARD,
        description="Payment method for the order (defaults to credit_card)"
    )
    currency: str = Field(
        default="USD",
        min_length=3,
        max_length=3,
        description="Currency code (ISO 4217)"
    )
    requested_delivery_date: Optional[datetime] = Field(
        None,
        description="Requested delivery date (must be future date)"
    )
    notes: Optional[str] = Field(
        None,
        max_length=1000,
        description="Special instructions or notes"
    )


class SalesOrderUpdate(BaseModel):
    """
    Model for updating an existing sales order.
    
    All fields are optional to allow partial updates.
    Some fields like order_id cannot be updated.
    """
    customer: Optional[Customer] = Field(
        None,
        description="Updated customer information"
    )
    items: Optional[List[OrderItem]] = Field(
        None,
        min_length=1,
        description="Updated list of order items"
    )
    status: Optional[OrderStatus] = Field(
        None,
        description="Updated order status"
    )
    payment_method: Optional[PaymentMethod] = Field(
        None,
        description="Updated payment method"
    )
    requested_delivery_date: Optional[datetime] = Field(
        None,
        description="Updated requested delivery date"
    )
    notes: Optional[str] = Field(
        None,
        max_length=1000,
        description="Updated notes or instructions"
    )


class SalesOrderResponse(BaseModel):
    """
    Model for API responses containing sales order data.
    
    Includes all order information plus computed totals and metadata
    for comprehensive order details in API responses.
    """
    order_id: str = Field(..., description="Unique order identifier")
    order_number: Optional[str] = Field(None, description="Human-readable order number")
    customer: Customer = Field(..., description="Customer information")
    items: List[OrderItem] = Field(..., description="Order items")
    status: OrderStatus = Field(..., description="Current order status")
    payment_method: Optional[PaymentMethod] = Field(None, description="Payment method")
    currency: str = Field(..., description="Order currency")
    order_date: datetime = Field(..., description="Order creation date")
    requested_delivery_date: Optional[datetime] = Field(None, description="Requested delivery date")
    notes: Optional[str] = Field(None, description="Order notes")
    created_at: datetime = Field(..., description="Record creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    # Computed fields for API response
    subtotal: Decimal = Field(..., description="Order subtotal before discounts and tax")
    total_discount: Decimal = Field(..., description="Total discount amount")
    total_tax: Decimal = Field(..., description="Total tax amount")
    total_amount: Decimal = Field(..., description="Final order total")
    item_count: int = Field(..., description="Total number of items")


class OrderListResponse(BaseModel):
    """
    Model for paginated list of orders response.
    
    Used for API endpoints that return multiple orders with pagination.
    """
    orders: List[SalesOrderResponse] = Field(
        ...,
        description="List of sales orders"
    )
    total_count: int = Field(
        ...,
        description="Total number of orders matching the query"
    )
    page: int = Field(
        ...,
        description="Current page number (1-based)"
    )
    page_size: int = Field(
        ...,
        description="Number of orders per page"
    )
    total_pages: int = Field(
        ...,
        description="Total number of pages available"
    )


class ErrorResponse(BaseModel):
    """
    Standard error response model.
    
    Used for all API error responses to provide consistent error information.
    """
    error: str = Field(
        ...,
        description="Error type or category"
    )
    message: str = Field(
        ...,
        description="Human-readable error message"
    )
    details: Optional[dict] = Field(
        None,
        description="Additional error details or validation errors"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the error occurred"
    )


class OrderStatusUpdate(BaseModel):
    """
    Model for updating order status.
    
    Used when updating only the status of an existing order.
    """
    status: OrderStatus = Field(..., description="New order status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "confirmed"
            }
        }


class SalesOrderResponse(BaseModel):
    """Response model for sales order operations."""
    order_id: str = Field(..., description="Unique order identifier")
    order_number: Optional[str] = Field(None, description="Human-readable order number")
    customer: Customer = Field(..., description="Customer information")
    items: List[OrderItem] = Field(..., description="List of order items")
    status: OrderStatus = Field(..., description="Current order status")
    payment_method: PaymentMethod = Field(..., description="Payment method")
    currency: str = Field(..., description="Currency code")
    subtotal_amount: Decimal = Field(..., description="Order subtotal amount")
    discount_amount: Decimal = Field(..., description="Total discount amount")
    tax_amount: Decimal = Field(..., description="Total tax amount")
    total_amount: Decimal = Field(..., description="Order total amount")
    item_count: int = Field(..., description="Total number of items")
    created_at: datetime = Field(..., description="Order creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    requested_delivery_date: Optional[datetime] = Field(None, description="Requested delivery date")
    notes: Optional[str] = Field(None, description="Order notes")


class SalesOrdersListResponse(BaseModel):
    """Response model for listing sales orders."""
    orders: List[SalesOrderResponse] = Field(..., description="List of orders")
    total_count: int = Field(..., description="Total number of orders matching criteria")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_previous: bool = Field(..., description="Whether there are previous pages")
