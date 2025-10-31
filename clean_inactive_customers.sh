#!/bin/bash

# Script to clean inactive customers (no orders in the past year)

LOG_FILE="/tmp/customer_cleanup_log.txt"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

# Run Django shell command to delete inactive customers
DELETED_COUNT=$(python3 manage.py shell <<EOF
from datetime import datetime, timedelta
from crm.models import Customer

one_year_ago = datetime.now() - timedelta(days=365)
inactive_customers = Customer.objects.filter(orders__isnull=True) | Customer.objects.exclude(orders__created_at__gte=one_year_ago)
inactive_customers = inactive_customers.distinct()
count = inactive_customers.count()
inactive_customers.delete()
print(count)
EOF
)

# Log result with timestamp
echo "\$TIMESTAMP - Deleted \$DELETED_COUNT inactive customers" >> "\$LOG_FILE"
