
PIXABAY_API_KEY = '51463181-ae1a56348f79b30e1237eb2c6'  # 🔴 Replace with your actual key
import os
import random
import time
import requests
from io import BytesIO
from decimal import Decimal
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from faker import Faker
from api.models import Product, ProductImage, ProductVariant, Category

fake = Faker()


COLORS = [
    ("Red", "#FF0000"),
    ("Black", "#000000"),
    ("Blue", "#0000FF"),
    ("Green", "#00FF00"),
    ("White", "#FFFFFF"),
    ("Yellow", "#FFFF00"),
    ("Pink", "#FFC0CB"),
    ("Grey", "#808080"),
]

# Fashion product types
MENS_FASHION = ["T-Shirt", "Shirt", "Pant", "Hoodie", "Coat"]
WOMENS_FASHION = ["T-Shirt", "Shirt", "Saree", "Chudithar", "Kurta", "Pant"]

def download_image_from_pixabay(search_term, retries=3):
    url = f"https://pixabay.com/api/?key={PIXABAY_API_KEY}&q={search_term.replace(' ', '+')}&image_type=photo&per_page=3"
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                continue
            data = response.json()
            if data.get('hits'):
                image_url = data['hits'][0]['largeImageURL']
                img_response = requests.get(image_url, timeout=10)
                if img_response.status_code == 200:
                    return ContentFile(img_response.content, name=f"{search_term.replace(' ', '_')}.jpg")
        except Exception as e:
            print(f"Retry {attempt + 1}/{retries} for '{search_term}' due to: {e}")
            time.sleep(1)
    return None

class Command(BaseCommand):
    help = "Generate 150 fashion-only products with real variant images from Pixabay"

    def handle(self, *args, **kwargs):
        TOTAL_PRODUCTS = 150
        existing_count = Product.objects.count()
        to_create = TOTAL_PRODUCTS - existing_count

        if to_create <= 0:
            self.stdout.write(self.style.WARNING("⚠️ 150 or more products already exist. Nothing to create."))
            return

        self.stdout.write(self.style.SUCCESS(f"🛠️ Creating {to_create} new fashion products (current: {existing_count})"))

        for i in range(to_create):
            is_men = random.choice([True, False])
            product_type = random.choice(MENS_FASHION if is_men else WOMENS_FASHION)
            gender = "Men" if is_men else "Women"
            category_name = f"{gender} {product_type}s"

            # Get or create category
            category, _ = Category.objects.get_or_create(name=category_name, defaults={"description": f"{gender} {product_type}s"})

            name = f"{gender} {product_type} {fake.word().capitalize()}"
            brand = fake.company()
            price = Decimal(random.randint(300, 1000))
            mrp = price + Decimal(random.randint(100, 300))
            stock = random.randint(10, 100)

            product = Product.objects.create(
                name=name,
                brand=brand,
                model_name=fake.word(),
                short_description=fake.sentence(),
                description=fake.text(),
                specifications={"Material": "Cotton", "Fit": "Regular"},
                key_features=["Breathable fabric", "Machine washable"],
                category=category,
                price=price,
                discount_price=price - Decimal(random.randint(50, 100)),
                mrp=mrp,
                stock=stock,
                sku=fake.unique.bothify(text='SKU-????-####'),
                weight=Decimal("0.4"),
                dimensions_length=Decimal("25.0"),
                dimensions_width=Decimal("20.0"),
                dimensions_height=Decimal("2.0"),
                condition='new',
                availability_status='in_stock',
                tags=[product_type.lower(), "fashion", gender.lower()],
                is_free_shipping=True,
                is_active=True
            )

            for index, (color, hex_code) in enumerate(COLORS[:random.randint(3, 6)]):  # 3-6 color variants
                variant_price = product.price + Decimal(random.randint(10, 50))
                variant_mrp = variant_price + Decimal(random.randint(50, 100))
                variant_sku = fake.unique.bothify(text='VAR-????-####')
                # Choose size list based on gender
                if product_type.lower() in ["shirt", "t-shirt", "hoodie", "coat", "kurta", "chudithar", "saree"]:
                    sizes = random.sample(["S", "M", "L", "XL", "XXL"], k=random.randint(2, 4))
                else:  # Likely pants
                    sizes = random.sample(["28", "30", "32", "34", "36", "38", "40"], k=random.randint(2, 4))

                variant = ProductVariant.objects.create(
                    product=product,
                    # variant_type="color",
                    variant_value=color,
                    price=variant_price,
                    mrp=variant_mrp,
                    stock=random.randint(5, 30),
                    sku=variant_sku,
                    is_active=True,
                    hex_color_code=hex_code,
                    size=sizes
                )

                # Download image
                search_term = f"{color} {gender} {product_type}"
                image_file = download_image_from_pixabay(search_term)

                if image_file:
                    ProductImage.objects.create(
                        product=product,
                        image=image_file,
                        alt_text=f"{color} {product.name}",
                        is_primary=(index == 0)
                    )

                time.sleep(1)  # avoid rate limit

            self.stdout.write(self.style.SUCCESS(f"✅ Created: {product.name}"))

