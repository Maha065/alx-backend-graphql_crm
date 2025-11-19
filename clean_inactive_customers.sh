#!/bin/bash

# Script to clean up inactive customers (no orders in the past year)
# Location: crm/cron_jobs/clean_inactive_customers.sh

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
LOG_FILE="/tmp/customer_cleanup_log.txt"

# Execute Django management command to delete inactive customers
DELETED_COUNT=$(cd "$(dirname "$0")/../.." && python manage.py shell << EOF
from django.utils import timezone
from datetime import timedelta
from crm.models import Customer
from django.db.models import Count, Q

# Calculate date one year ago
one_year_ago = timezone.now() - timedelta(days=365)

# Find and delete customers with no orders since a year ago
inactive_customers = Customer.objects.annotate(
    order_count=Count('orders', filter=Q(orders__created_at__gte=one_year_ago))
).filter(order_count=0)

deleted_count = inactive_customers.count()
inactive_customers.delete()

print(deleted_count)
EOF
)

# Log the result with timestamp
echo "[$TIMESTAMP] Deleted $DELETED_COUNT inactive customers" >> "$LOG_FILE"

exit 0
