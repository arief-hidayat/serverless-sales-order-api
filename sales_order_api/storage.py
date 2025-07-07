"""
DynamoDB storage implementation for Sales Order API

This module provides a DynamoDB-based storage layer that maintains
the same interface as the in-memory storage while providing
persistent, scalable, serverless storage.
"""

import os
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import uuid4

import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.metrics import MetricUnit

from models import SalesOrder, OrderStatus

logger = Logger()
tracer = Tracer()
metrics = Metrics()


class DynamoDBOrderStorage:
    """
    DynamoDB-based storage for sales orders.
    
    Provides persistent storage with the same interface as in-memory storage,
    using DynamoDB for scalable, serverless data persistence.
    """
    
    def __init__(self):
        """Initialize DynamoDB connection and table reference."""
        self.dynamodb = boto3.resource('dynamodb')
        self.table_name = os.environ.get('ORDERS_TABLE')
        if not self.table_name:
            raise ValueError("ORDERS_TABLE environment variable is required")
        
        self.table = self.dynamodb.Table(self.table_name)
        logger.info(f"Initialized DynamoDB storage with table: {self.table_name}")
    
    def _serialize_order(self, order: SalesOrder) -> Dict[str, Any]:
        """
        Serialize SalesOrder to DynamoDB item format.
        
        Args:
            order: SalesOrder instance to serialize
            
        Returns:
            Dictionary suitable for DynamoDB storage
        """
        # Convert order to dict and handle serialization
        order_dict = order.model_dump()
        
        # Convert datetime objects to ISO strings for DynamoDB
        def convert_datetimes(obj):
            if isinstance(obj, dict):
                return {k: convert_datetimes(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_datetimes(item) for item in obj]
            elif isinstance(obj, datetime):
                return obj.isoformat()
            else:
                return obj
        
        order_dict = convert_datetimes(order_dict)
        
        # Create DynamoDB item with GSI attributes
        item = {
            'order_id': order.order_id,
            'customer_id': order.customer.customer_id,
            'status': order.status.value,
            'created_at': order.created_at.isoformat(),
            'updated_at': order.updated_at.isoformat(),
            'date_partition': order.created_at.strftime('%Y-%m'),  # For date-based queries
            'order_data': order_dict
        }
        
        return item
    
    def _deserialize_order(self, item: Dict[str, Any]) -> SalesOrder:
        """
        Deserialize DynamoDB item to SalesOrder.
        
        Args:
            item: DynamoDB item dictionary
            
        Returns:
            SalesOrder instance
        """
        return SalesOrder(**item['order_data'])
    
    @tracer.capture_method
    def create_order(self, order: SalesOrder) -> None:
        """
        Create a new order in DynamoDB.
        
        Args:
            order: SalesOrder instance to store
            
        Raises:
            ClientError: If DynamoDB operation fails
        """
        try:
            item = self._serialize_order(order)
            
            # Use condition to prevent overwriting existing orders
            self.table.put_item(
                Item=item,
                ConditionExpression=Attr('order_id').not_exists()
            )
            
            logger.info(f"Created order: {order.order_id}")
            metrics.add_metric(name="OrderCreated", unit=MetricUnit.Count, value=1)
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                logger.error(f"Order {order.order_id} already exists")
                raise ValueError(f"Order {order.order_id} already exists")
            else:
                logger.error(f"Failed to create order {order.order_id}: {e}")
                metrics.add_metric(name="OrderCreateError", unit=MetricUnit.Count, value=1)
                raise
    
    @tracer.capture_method
    def get_order(self, order_id: str) -> Optional[SalesOrder]:
        """
        Retrieve an order by ID.
        
        Args:
            order_id: Unique order identifier
            
        Returns:
            SalesOrder instance if found, None otherwise
        """
        try:
            response = self.table.get_item(
                Key={'order_id': order_id},
                ConsistentRead=True  # Strong consistency for individual reads
            )
            
            if 'Item' in response:
                order = self._deserialize_order(response['Item'])
                logger.info(f"Retrieved order: {order_id}")
                metrics.add_metric(name="OrderRetrieved", unit=MetricUnit.Count, value=1)
                return order
            else:
                logger.info(f"Order not found: {order_id}")
                metrics.add_metric(name="OrderNotFound", unit=MetricUnit.Count, value=1)
                return None
                
        except ClientError as e:
            logger.error(f"Failed to retrieve order {order_id}: {e}")
            metrics.add_metric(name="OrderRetrieveError", unit=MetricUnit.Count, value=1)
            raise
    
    @tracer.capture_method
    def update_order(self, order: SalesOrder) -> None:
        """
        Update an existing order.
        
        Args:
            order: Updated SalesOrder instance
            
        Raises:
            ValueError: If order doesn't exist
            ClientError: If DynamoDB operation fails
        """
        try:
            # Update the updated_at timestamp
            order.updated_at = datetime.now(timezone.utc)
            item = self._serialize_order(order)
            
            # Use condition to ensure order exists
            self.table.put_item(
                Item=item,
                ConditionExpression=Attr('order_id').exists()
            )
            
            logger.info(f"Updated order: {order.order_id}")
            metrics.add_metric(name="OrderUpdated", unit=MetricUnit.Count, value=1)
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                logger.error(f"Order {order.order_id} not found for update")
                raise ValueError(f"Order {order.order_id} not found")
            else:
                logger.error(f"Failed to update order {order.order_id}: {e}")
                metrics.add_metric(name="OrderUpdateError", unit=MetricUnit.Count, value=1)
                raise
    
    @tracer.capture_method
    def delete_order(self, order_id: str) -> bool:
        """
        Delete an order by ID.
        
        Args:
            order_id: Unique order identifier
            
        Returns:
            True if order was deleted, False if not found
        """
        try:
            self.table.delete_item(
                Key={'order_id': order_id},
                ConditionExpression=Attr('order_id').exists()
            )
            
            logger.info(f"Deleted order: {order_id}")
            metrics.add_metric(name="OrderDeleted", unit=MetricUnit.Count, value=1)
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                logger.info(f"Order not found for deletion: {order_id}")
                metrics.add_metric(name="OrderDeleteNotFound", unit=MetricUnit.Count, value=1)
                return False
            else:
                logger.error(f"Failed to delete order {order_id}: {e}")
                metrics.add_metric(name="OrderDeleteError", unit=MetricUnit.Count, value=1)
                raise
    
    @tracer.capture_method
    def list_orders(
        self,
        status: Optional[str] = None,
        customer_id: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        page_size: int = 10,
        last_evaluated_key: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        List orders with optional filtering and pagination.
        
        Args:
            status: Filter by order status
            customer_id: Filter by customer ID
            from_date: Filter orders created after this date
            to_date: Filter orders created before this date
            page_size: Maximum number of items to return
            last_evaluated_key: Pagination token from previous request
            
        Returns:
            Dictionary containing orders list and pagination info
        """
        try:
            query_params = {
                'Limit': page_size
            }
            
            if last_evaluated_key:
                query_params['ExclusiveStartKey'] = last_evaluated_key
            
            # Choose the most efficient query strategy
            if customer_id:
                # Use CustomerIndex GSI
                query_params.update({
                    'IndexName': 'CustomerIndex',
                    'KeyConditionExpression': Key('customer_id').eq(customer_id)
                })
                
                # Add date range filter if specified
                if from_date or to_date:
                    if from_date and to_date:
                        query_params['KeyConditionExpression'] &= Key('created_at').between(
                            from_date.isoformat(), to_date.isoformat()
                        )
                    elif from_date:
                        query_params['KeyConditionExpression'] &= Key('created_at').gte(from_date.isoformat())
                    elif to_date:
                        query_params['KeyConditionExpression'] &= Key('created_at').lte(to_date.isoformat())
                
                response = self.table.query(**query_params)
                
            elif status:
                # Use StatusIndex GSI
                query_params.update({
                    'IndexName': 'StatusIndex',
                    'KeyConditionExpression': Key('status').eq(status)
                })
                
                # Add date range filter if specified
                if from_date or to_date:
                    if from_date and to_date:
                        query_params['KeyConditionExpression'] &= Key('created_at').between(
                            from_date.isoformat(), to_date.isoformat()
                        )
                    elif from_date:
                        query_params['KeyConditionExpression'] &= Key('created_at').gte(from_date.isoformat())
                    elif to_date:
                        query_params['KeyConditionExpression'] &= Key('created_at').lte(to_date.isoformat())
                
                response = self.table.query(**query_params)
                
            else:
                # Scan all items (less efficient, use with caution)
                filter_expressions = []
                
                if from_date:
                    filter_expressions.append(Attr('created_at').gte(from_date.isoformat()))
                if to_date:
                    filter_expressions.append(Attr('created_at').lte(to_date.isoformat()))
                
                if filter_expressions:
                    filter_expr = filter_expressions[0]
                    for expr in filter_expressions[1:]:
                        filter_expr &= expr
                    query_params['FilterExpression'] = filter_expr
                
                response = self.table.scan(**query_params)
            
            # Deserialize orders
            orders = [self._deserialize_order(item) for item in response['Items']]
            
            # Sort by created_at descending (most recent first)
            orders.sort(key=lambda x: x.created_at, reverse=True)
            
            result = {
                'orders': orders,
                'count': len(orders),
                'last_evaluated_key': response.get('LastEvaluatedKey')
            }
            
            logger.info(f"Listed {len(orders)} orders with filters: status={status}, customer_id={customer_id}")
            metrics.add_metric(name="OrdersListed", unit=MetricUnit.Count, value=len(orders))
            
            return result
            
        except ClientError as e:
            logger.error(f"Failed to list orders: {e}")
            metrics.add_metric(name="OrderListError", unit=MetricUnit.Count, value=1)
            raise
    
    @tracer.capture_method
    def count_orders(self) -> int:
        """
        Get total count of orders.
        
        Returns:
            Total number of orders in the table
        """
        try:
            # Use scan to get actual count (for small tables)
            response = self.table.scan(Select='COUNT')
            count = response['Count']
            
            logger.info(f"Total orders count: {count}")
            return count
            
        except ClientError as e:
            logger.error(f"Failed to count orders: {e}")
            metrics.add_metric(name="OrderCountError", unit=MetricUnit.Count, value=1)
            raise


# Global storage instance
storage = DynamoDBOrderStorage()
