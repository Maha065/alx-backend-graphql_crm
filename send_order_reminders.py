#!/usr/bin/env python3

import datetime
import logging
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

# Setup logging
LOG_FILE = "/tmp/order_reminders_log.txt"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
)

# GraphQL endpoint
transport = RequestsHTTPTransport(
    url="http://localhost:8000/graphql",
    verify=False,
    retries=3,
)

client = Client(transport=transport, fetch_schema_from_transport=False)

# Calculate date range (last 7 days)
today = datetime.date.today()
week_ago = today - datetime.timedelta(days=7)

# GraphQL query to find pending orders within last 7 days
query = gql("""
query GetRecentPendingOrders($fromDate: Date!, $toDate: Date!) {
  orders(orderDate_Gte: $fromDate, orderDate_Lte: $toDate, status: "PENDING") {
    id
    customer {
      email
    }
  }
}
""")

# Execute query
try:
    response = client.execute(query, variable_values={"fromDate": str(week_ago), "toDate": str(today)})

    orders = response.get("orders", [])
    for order in orders:
        order_id = order.get("id")
        email = order.get("customer", {}).get("email")
        logging.info(f"Pending Order ID: {order_id}, Customer Email: {email}")

    print("Order reminders processed!")

except Exception as e:
    logging.error(f"Error while processing order reminders: {e}")
    print("Failed to process order reminders!")
