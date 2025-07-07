#!/usr/bin/env python3
"""
Simple test script to verify the Sales Order API functionality.
This script tests the basic CRUD operations and validates responses.
"""

import json
import requests
import sys
from datetime import datetime
from decimal import Decimal


def test_api(base_url: str, api_key: str = None):
    """Test the Sales Order API endpoints."""
    print(f"Testing Sales Order API at: {base_url}")
    if api_key:
        print(f"Using API Key: {api_key[:8]}...")
    
    # Headers for authenticated requests
    auth_headers = {"X-API-Key": api_key} if api_key else {}
    
    # Test health check (no auth required)
    print("\n1. Testing health check...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            health_data = response.json()
            print(f"   Service: {health_data.get('service')}")
            print(f"   Status: {health_data.get('status')}")
            print("   ✅ Health check passed")
        else:
            print("   ❌ Health check failed")
            return False
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
        return False
    
    # Test OpenAPI spec (no auth required)
    print("\n2. Testing OpenAPI specification...")
    try:
        response = requests.get(f"{base_url}/openapi.json")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            openapi_data = response.json()
            print(f"   OpenAPI Version: {openapi_data.get('openapi')}")
            print(f"   API Title: {openapi_data.get('info', {}).get('title')}")
            print("   ✅ OpenAPI spec retrieved")
        else:
            print("   ❌ OpenAPI spec failed")
    except Exception as e:
        print(f"   ❌ OpenAPI spec error: {e}")
    
    # Test creating an order (requires auth)
    print("\n3. Testing order creation...")
    sample_order = {
        "customer": {
            "customer_id": "CUST001",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "+1-555-123-4567",
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
        "currency": "USD",
        "notes": "Test order from API validation script"
    }
    
    try:
        headers = {"Content-Type": "application/json"}
        headers.update(auth_headers)
        
        response = requests.post(
            f"{base_url}/orders",
            json=sample_order,
            headers=headers
        )
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 201:
            order_data = response.json()
            order_id = order_data.get('order_id')
            print(f"   Order ID: {order_id}")
            print(f"   Total Amount: ${order_data.get('total_amount')}")
            print(f"   Status: {order_data.get('status')}")
            print("   ✅ Order created successfully")
            
            # Test getting the order (requires auth)
            print("\n4. Testing order retrieval...")
            get_response = requests.get(f"{base_url}/orders/{order_id}", headers=auth_headers)
            print(f"   Status: {get_response.status_code}")
            
            if get_response.status_code == 200:
                retrieved_order = get_response.json()
                print(f"   Retrieved Order ID: {retrieved_order.get('order_id')}")
                print(f"   Customer: {retrieved_order.get('customer', {}).get('first_name')} {retrieved_order.get('customer', {}).get('last_name')}")
                print("   ✅ Order retrieved successfully")
            else:
                print("   ❌ Order retrieval failed")
            
            # Test updating order status (requires auth)
            print("\n5. Testing order status update...")
            status_update = {"status": "confirmed"}
            status_headers = {"Content-Type": "application/json"}
            status_headers.update(auth_headers)
            
            status_response = requests.patch(
                f"{base_url}/orders/{order_id}/status",
                json=status_update,
                headers=status_headers
            )
            print(f"   Status: {status_response.status_code}")
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                print(f"   New Status: {status_data.get('status')}")
                print(f"   Previous Status: {status_data.get('previous_status')}")
                print("   ✅ Order status updated successfully")
            else:
                print("   ❌ Order status update failed")
            
            # Test listing orders (requires auth)
            print("\n6. Testing order listing...")
            list_response = requests.get(f"{base_url}/orders", headers=auth_headers)
            print(f"   Status: {list_response.status_code}")
            
            if list_response.status_code == 200:
                list_data = list_response.json()
                print(f"   Total Orders: {list_data.get('total_count')}")
                print(f"   Orders in Response: {len(list_data.get('orders', []))}")
                print("   ✅ Order listing successful")
            else:
                print("   ❌ Order listing failed")
            
            # Test deleting the order (cleanup, requires auth)
            print("\n7. Testing order deletion...")
            delete_response = requests.delete(f"{base_url}/orders/{order_id}", headers=auth_headers)
            print(f"   Status: {delete_response.status_code}")
            
            if delete_response.status_code == 200:
                print("   ✅ Order deleted successfully")
            else:
                print("   ❌ Order deletion failed")
            
            return True
            
        elif response.status_code == 403:
            print("   ❌ Order creation failed: API key required or invalid")
            print("   Please provide a valid API key using: python test_api.py <base_url> <api_key>")
            return False
        else:
            print(f"   ❌ Order creation failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Order creation error: {e}")
        return False


def main():
    """Main function to run API tests."""
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python test_api.py <base_url> [api_key]")
        print("Example: python test_api.py http://localhost:3000")
        print("Example: python test_api.py https://your-api-gateway-url.amazonaws.com/Prod your-api-key")
        sys.exit(1)
    
    base_url = sys.argv[1].rstrip('/')
    api_key = sys.argv[2] if len(sys.argv) == 3 else None
    
    if not api_key:
        print("⚠️  Warning: No API key provided. Only public endpoints will be tested.")
        print("   For full testing, provide an API key as the second argument.")
    
    print("=" * 60)
    print("Sales Order API Test Suite")
    print("=" * 60)
    
    success = test_api(base_url, api_key)
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 All tests passed! The Sales Order API is working correctly.")
    else:
        print("❌ Some tests failed. Please check the API implementation.")
        if not api_key:
            print("💡 Tip: Provide an API key for full testing of protected endpoints.")
    print("=" * 60)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
