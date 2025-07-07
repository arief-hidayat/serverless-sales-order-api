#!/usr/bin/env python3
"""
Generate sample orders for the Sales Order API

This script creates 20 realistic sample orders using the 10 supermarket items.
Each order contains 1-5 random items with realistic quantities and customer data.
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

# Sample customer data
CUSTOMERS = [
    {
        "customer_id": "CUST001",
        "first_name": "John",
        "last_name": "Smith",
        "email": "john.smith@email.com",
        "phone": "+1-555-123-4567",
        "billing_address": {
            "street": "123 Main St",
            "city": "Springfield",
            "state": "IL",
            "postal_code": "62701",
            "country": "USA"
        }
    },
    {
        "customer_id": "CUST002",
        "first_name": "Sarah",
        "last_name": "Johnson",
        "email": "sarah.johnson@email.com",
        "phone": "+1-555-234-5678",
        "billing_address": {
            "street": "456 Oak Ave",
            "city": "Madison",
            "state": "WI",
            "postal_code": "53703",
            "country": "USA"
        }
    },
    {
        "customer_id": "CUST003",
        "first_name": "Michael",
        "last_name": "Brown",
        "email": "michael.brown@email.com",
        "phone": "+1-555-345-6789",
        "billing_address": {
            "street": "789 Pine Rd",
            "city": "Austin",
            "state": "TX",
            "postal_code": "73301",
            "country": "USA"
        }
    },
    {
        "customer_id": "CUST004",
        "first_name": "Emily",
        "last_name": "Davis",
        "email": "emily.davis@email.com",
        "phone": "+1-555-456-7890",
        "billing_address": {
            "street": "321 Elm St",
            "city": "Portland",
            "state": "OR",
            "postal_code": "97201",
            "country": "USA"
        }
    },
    {
        "customer_id": "CUST005",
        "first_name": "David",
        "last_name": "Wilson",
        "email": "david.wilson@email.com",
        "phone": "+1-555-567-8901",
        "billing_address": {
            "street": "654 Maple Dr",
            "city": "Denver",
            "state": "CO",
            "postal_code": "80202",
            "country": "USA"
        }
    }
]

PAYMENT_METHODS = ["credit_card", "debit_card", "paypal", "bank_transfer"]

def load_sample_items():
    """Load sample items from JSON file"""
    items_file = Path(__file__).parent.parent / "data" / "sample_items.json"
    with open(items_file, 'r') as f:
        return json.load(f)

def generate_order_items(available_items, num_items=None):
    """Generate random order items"""
    if num_items is None:
        num_items = random.randint(1, 5)
    
    selected_items = random.sample(available_items, min(num_items, len(available_items)))
    order_items = []
    
    for item in selected_items:
        # Generate realistic quantities based on item type
        if "milk" in item["product_name"].lower() or "juice" in item["product_name"].lower():
            quantity = random.randint(1, 2)
        elif "bread" in item["product_name"].lower() or "cheese" in item["product_name"].lower():
            quantity = random.randint(1, 3)
        elif "meat" in item["sku"].lower():
            quantity = random.randint(1, 3)
        else:
            quantity = random.randint(1, 4)
        
        # Occasionally add discounts
        discount_percent = 0
        if random.random() < 0.2:  # 20% chance of discount
            discount_percent = random.choice([5, 10, 15, 20])
        
        order_item = {
            "item_id": item["item_id"],
            "product_name": item["product_name"],
            "sku": item["sku"],
            "quantity": quantity,
            "unit_price": item["unit_price"]
        }
        
        # Only add discount if it's not 0 (let default handle 0%)
        if discount_percent > 0:
            order_item["discount_percent"] = discount_percent
            
        # Tax will use default 10%
        
        order_items.append(order_item)
    
    return order_items

def generate_sample_orders(num_orders=20):
    """Generate sample orders"""
    available_items = load_sample_items()
    orders = []
    
    for i in range(num_orders):
        # Select random customer
        customer = random.choice(CUSTOMERS).copy()
        
        # Sometimes add shipping address
        if random.random() < 0.3:  # 30% chance of different shipping address
            customer["shipping_address"] = {
                "street": f"{random.randint(100, 999)} {random.choice(['First', 'Second', 'Third'])} St",
                "city": customer["billing_address"]["city"],
                "state": customer["billing_address"]["state"],
                "postal_code": customer["billing_address"]["postal_code"],
                "country": "USA"
            }
        
        # Generate order items
        items = generate_order_items(available_items)
        
        # Create order
        order = {
            "customer": customer,
            "items": items,
            "payment_method": random.choice(PAYMENT_METHODS)
        }
        
        # Sometimes add order number
        if random.random() < 0.7:  # 70% chance of order number
            order["order_number"] = f"ORD-{2024}-{(i+1):04d}"
        
        # Sometimes add notes
        if random.random() < 0.3:  # 30% chance of notes
            notes = random.choice([
                "Please deliver to front door",
                "Call before delivery",
                "Leave at doorstep if no answer",
                "Fragile items - handle with care",
                "Rush delivery requested"
            ])
            order["notes"] = notes
        
        # Sometimes add requested delivery date (1-7 days from now)
        if random.random() < 0.4:  # 40% chance of requested delivery
            delivery_date = datetime.now() + timedelta(days=random.randint(1, 7))
            order["requested_delivery_date"] = delivery_date.isoformat() + "Z"
        
        orders.append(order)
    
    return orders

def main():
    """Generate and save sample orders"""
    print("🏪 Generating sample supermarket orders...")
    
    orders = generate_sample_orders(20)
    
    # Save to file
    output_file = Path(__file__).parent.parent / "data" / "sample_orders.json"
    with open(output_file, 'w') as f:
        json.dump(orders, f, indent=2)
    
    print(f"✅ Generated {len(orders)} sample orders")
    print(f"📁 Saved to: {output_file}")
    
    # Print summary
    total_items = sum(len(order["items"]) for order in orders)
    print(f"📊 Summary:")
    print(f"   - Total orders: {len(orders)}")
    print(f"   - Total items: {total_items}")
    print(f"   - Average items per order: {total_items / len(orders):.1f}")
    
    # Show first order as example
    print(f"\n📋 Example order:")
    print(json.dumps(orders[0], indent=2))

if __name__ == "__main__":
    main()
