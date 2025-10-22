import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alx_backend_graphql_crm.settings')
django.setup()

from crm.models import Customer, Product

def seed():
    customers = [
        {"name": "John Doe", "email": "john@example.com", "phone": "+1234567890"},
        {"name": "Jane Smith", "email": "jane@example.com"},
    ]
    for c in customers:
        Customer.objects.get_or_create(**c)

    products = [
        {"name": "Phone", "price": 499.99, "stock": 20},
        {"name": "Tablet", "price": 299.99, "stock": 15},
    ]
    for p in products:
        Product.objects.get_or_create(**p)

    print("Database seeded successfully!")

if __name__ == "__main__":
    seed()
