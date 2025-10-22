import graphene
from graphene_django import DjangoObjectType
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Customer, Product, Order

# ===== GraphQL Object Types =====

class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = "__all__"


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = "__all__"


class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = "__all__"


# ===== Mutations =====

# 1️⃣ CreateCustomer
class CreateCustomer(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        email = graphene.String(required=True)
        phone = graphene.String()

    customer = graphene.Field(CustomerType)
    message = graphene.String()

    @staticmethod
    def mutate(root, info, name, email, phone=None):
        if Customer.objects.filter(email=email).exists():
            raise Exception("Email already exists")

        customer = Customer(name=name, email=email, phone=phone or "")
        try:
            customer.full_clean()
            customer.save()
        except ValidationError as e:
            raise Exception(str(e))

        return CreateCustomer(customer=customer, message="Customer created successfully!")


# 2️⃣ BulkCreateCustomers
class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        input = graphene.List(
            graphene.JSONString, required=True,
            description="List of customers with name, email, phone"
        )

    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    @staticmethod
    def mutate(root, info, input):
        created_customers = []
        errors = []

        with transaction.atomic():
            for data in input:
                name = data.get("name")
                email = data.get("email")
                phone = data.get("phone", "")

                if not name or not email:
                    errors.append(f"Missing required fields for {data}")
                    continue

                if Customer.objects.filter(email=email).exists():
                    errors.append(f"Duplicate email: {email}")
                    continue

                try:
                    customer = Customer(name=name, email=email, phone=phone)
                    customer.full_clean()
                    customer.save()
                    created_customers.append(customer)
                except ValidationError as e:
                    errors.append(f"{email}: {e}")

        return BulkCreateCustomers(customers=created_customers, errors=errors)


# 3️⃣ CreateProduct
class CreateProduct(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        price = graphene.Float(required=True)
        stock = graphene.Int(required=False, default_value=0)

    product = graphene.Field(ProductType)

    @staticmethod
    def mutate(root, info, name, price, stock=0):
        if price <= 0:
            raise Exception("Price must be positive")
        if stock < 0:
            raise Exception("Stock cannot be negative")

        product = Product(name=name, price=price, stock=stock)
        product.save()
        return CreateProduct(product=product)


# 4️⃣ CreateOrder
class CreateOrder(graphene.Mutation):
    class Arguments:
        customer_id = graphene.ID(required=True)
        product_ids = graphene.List(graphene.ID, required=True)
        order_date = graphene.DateTime(required=False)

    order = graphene.Field(OrderType)

    @staticmethod
    def mutate(root, info, customer_id, product_ids, order_date=None):
        try:
            customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            raise Exception("Invalid customer ID")

        products = Product.objects.filter(id__in=product_ids)
        if not products.exists():
            raise Exception("Invalid product IDs")
        if len(products) == 0:
            raise Exception("At least one product must be selected")

        with transaction.atomic():
            order = Order.objects.create(customer=customer, order_date=order_date or None)
            order.products.set(products)
            order.total_amount = sum([p.price for p in products])
            order.save()

        return CreateOrder(order=order)


# ===== Root Mutation and Query =====
class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()


class Query(graphene.ObjectType):
    customers = graphene.List(CustomerType)
    products = graphene.List(ProductType)
    orders = graphene.List(OrderType)

    def resolve_customers(root, info):
        return Customer.objects.all()

    def resolve_products(root, info):
        return Product.objects.all()

    def resolve_orders(root, info):
        return Order.objects.all()

