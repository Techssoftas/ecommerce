import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from api.models import AlphaNumericFieldfive,Category, Product, ProductVariant, Order, OrderItem, Payment, ShippingAddress
from decimal import Decimal
import string

class Command(BaseCommand):
    help = 'Generates 50 realistic fashion orders for user ID 1 using existing categories and products'

    def handle(self, *args, **kwargs):
        CustomUser = get_user_model()

        # Fetch user with ID 1
        try:
            user = CustomUser.objects.get(id=1)
        except CustomUser.DoesNotExist:
            self.stdout.write(self.style.ERROR('User with ID 1 does not exist. Please ensure the user exists before running this command.'))
            return

        # Fetch existing categories (IDs 5–15)
        category_ids = range(5, 16)  # 5 to 15 inclusive
        categories = Category.objects.filter(id__in=category_ids)
        if categories.count() != 11:
            self.stdout.write(self.style.ERROR('Not all categories (IDs 5–15) found. Please ensure all categories exist.'))
            return

        # Fetch existing products (IDs 249–256)
        product_ids = range(249, 257)  # 249 to 256 inclusive
        products = Product.objects.filter(id__in=product_ids)
        if products.count() != 8:
            self.stdout.write(self.style.ERROR('Not all products (IDs 249–256) found. Please ensure all products exist.'))
            return

        # Create variants (colors and sizes) for each product if not already present
        variants = []
        colors = ['Blue', 'Black', 'White', 'Red']
        sizes = ['S', 'M', 'L', 'XL']
        for product in products:
            for color in colors:
                for size in sizes:
                    variant, created = ProductVariant.objects.get_or_create(
                        product=product,
                        variant_type='color',
                        variant_value=f'{color} {size}',
                        defaults={
                            'price': product.price + Decimal(random.uniform(-100, 100)),
                            'stock': random.randint(10, 50),
                            'sku': f'{product.sku}-{color[:3].upper()}{size}',
                            'is_active': True,
                            'hex_color_code': random.choice(['#0000FF', '#000000', '#FFFFFF', '#FF0000']),
                        }
                    )
                    if created:
                        variants.append(variant)
                    else:
                        variants.append(variant)  # Include existing variants

        # Create or get shipping address for user
        shipping_address, _ = ShippingAddress.objects.get_or_create(
            user=user,
            address_line1='123 Fashion Street',
            city='Style City',
            state='Style State',
            postal_code='400001',
            country='India',
            defaults={'phone': user.phone or '+919876543210', 'is_default': True}
        )

        # Create 50 orders
        order_statuses = [status[0] for status in Order.ORDER_STATUS]
        payment_methods = [method[0] for method in Payment.PAYMENT_METHODS]
        payment_statuses = [status[0] for status in Payment.PAYMENT_STATUS]

        for i in range(50):
            status = random.choice(order_statuses)
            created_at = timezone.now() - timedelta(days=random.randint(0, 365))
            total_amount = Decimal(0)

            # Create order
            order = Order.objects.create(
                user=user,
                order_number=AlphaNumericFieldfive.generate_alphanumeric(),
                status=status,
                total_amount=0,  # Will update after adding items
                shipping_address=shipping_address,
                billing_address='123 Fashion Street, Style City',
                phone=user.phone or '+919876543210',
                email=user.email,
                created_at=created_at,
                updated_at=created_at if status != 'delivered' else created_at + timedelta(days=random.randint(3, 10)),
            )

            # Add 1-3 items to the order
            num_items = random.randint(1, 3)
            items = random.sample(list(products) + variants, num_items)
            for item in items:
                quantity = random.randint(1, 5)
                price = item.price if hasattr(item, 'price') else item.get_price
                total_amount += price * quantity

                OrderItem.objects.create(
                    order=order,
                    product=item if isinstance(item, Product) else item.product,
                    variant=item if isinstance(item, ProductVariant) else None,
                    quantity=quantity,
                    price=price,
                )

            # Update total_amount
            order.total_amount = total_amount
            order.save()

            # Create payment if not COD
            if random.choice([True, False]) or status in ['delivered', 'confirmed']:
                Payment.objects.create(
                    order=order,
                    payment_method=random.choice(payment_methods),
                    amount=total_amount,
                    status='completed' if status == 'delivered' else random.choice(payment_statuses),
                    transaction_id=f'TXN{random.randint(100000, 999999)}' if status != 'cancelled' else None,
                )

        self.stdout.write(self.style.SUCCESS(f'Successfully generated 50 fashion orders for user ID {user.id}'))