from django.core.management.base import BaseCommand, CommandError
from api.models import CustomUser, Product, Wishlist
import random

class Command(BaseCommand):
    help = 'Adds up to 20 random products to the wishlist for user with email s@gmsil.com'

    def handle(self, *args, **options):
        email = 's@gmsil.com'
        max_products = 20

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            raise CommandError(f'User with email {email} does not exist')

        # Get all active products
        products = Product.objects.filter(is_active=True)
        if not products.exists():
            raise CommandError('No active products found in the database')

        # Select up to 20 random products
        product_count = products.count()
        select_count = min(max_products, product_count)
        selected_products = random.sample(list(products), select_count)

        added_count = 0
        skipped_count = 0

        for product in selected_products:
            # Check if the product is already in the user's wishlist
            if Wishlist.objects.filter(user=user, product=product).exists():
                self.stdout.write(f'Product "{product.name}" is already in the wishlist for user {email}')
                skipped_count += 1
                continue

            # Add to wishlist
            Wishlist.objects.create(user=user, product=product)
            self.stdout.write(f'Added product "{product.name}" to wishlist for user {email}')
            added_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'Summary: Added {added_count} products, skipped {skipped_count} already wishlisted products for user {email}'
        ))