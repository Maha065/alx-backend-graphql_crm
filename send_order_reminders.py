#!/usr/bin/env python
"""
Script to send order reminders for pending orders from the last 7 days.
Location: crm/cron_jobs/send_order_reminders.py
"""

import os
import sys
import django
from datetime import datetime, timedelta
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

# Setup Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')
django.setup()

# GraphQL Endpoint
GRAPHQL_ENDPOINT = 'http://localhost:8000/graphql'
LOG_FILE = '/tmp/order_reminders_log.txt'

# GraphQL Query for pending orders within the last 7 days
QUERY_PENDING_ORDERS = gql("""
    query GetPendingOrders($minDate: DateTime!) {
        allOrders(status: "pending") {
            id
            customer {
                email
            }
            createdAt
            status
        }
    }
""")

def fetch_pending_orders():
    """Fetch pending orders from the last 7 days using GraphQL"""
    try:
        # Setup GraphQL client
        transport = RequestsHTTPTransport(
            url=GRAPHQL_ENDPOINT,
            verify=True,
            retries=3,
        )
        client = Client(transport=transport, fetch_schema_from_transport=True)
        
        # Execute query
        result = client.execute(QUERY_PENDING_ORDERS)
        
        return result.get('allOrders', [])
    
    except Exception as e:
        print(f"Error connecting to GraphQL endpoint: {e}", file=sys.stderr)
        return []

def filter_orders_by_date(orders, days=7):
    """Filter orders created within the last N days"""
    now = datetime.now()
    cutoff_date = now - timedelta(days=days)
    
    filtered_orders = []
    for order in orders:
        try:
            # Parse order creation date
            order_date = datetime.fromisoformat(order['createdAt'].replace('Z', '+00:00'))
            
            # Convert to naive datetime for comparison
            if order_date.tzinfo is not None:
                order_date = order_date.replace(tzinfo=None)
            
            if order_date >= cutoff_date:
                filtered_orders.append(order)
        except (ValueError, KeyError) as e:
            print(f"Error parsing order date: {e}", file=sys.stderr)
            continue
    
    return filtered_orders

def log_order_reminder(order_id, customer_email, timestamp):
    """Log order reminder to file with timestamp"""
    try:
        with open(LOG_FILE, 'a') as f:
            log_entry = f"[{timestamp}] Order ID: {order_id}, Customer Email: {customer_email}\n"
            f.write(log_entry)
    except IOError as e:
        print(f"Error writing to log file: {e}", file=sys.stderr)

def main():
    """Main function to process order reminders"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Fetch pending orders from GraphQL endpoint
    orders = fetch_pending_orders()
    
    if not orders:
        print("No orders found from GraphQL endpoint")
        return
    
    # Filter orders from the last 7 days
    recent_orders = filter_orders_by_date(orders, days=7)
    
    # Log each order reminder
    for order in recent_orders:
        try:
            order_id = order.get('id')
            customer_email = order.get('customer', {}).get('email', 'N/A')
            log_order_reminder(order_id, customer_email, timestamp)
        except (KeyError, TypeError) as e:
            print(f"Error processing order: {e}", file=sys.stderr)
            continue
    
    print("Order reminders processed!")

if __name__ == '__main__':
    main()
