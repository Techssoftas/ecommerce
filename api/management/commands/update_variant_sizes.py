import random
from django.core.management.base import BaseCommand
from api.models import ProductVariant

class Command(BaseCommand):
    help = 'Update all ProductVariant size fields with a random list of sizes (as list, not dict)'

    def handle(self, *args, **options):
        size_options = ['s', 'm', 'l', 'xl', 'xxl', '36', '38', '40', '44']
        total_updated = 0

        variants = ProductVariant.objects.all()
        for variant in variants:
            random_sizes = random.sample(size_options, k=random.randint(2, 4))  # 2 to 4 random sizes
            variant.size = random_sizes  # Store as plain list
            variant.save()
            total_updated += 1
            self.stdout.write(self.style.SUCCESS(
                f"✅ Updated variant {variant.id} with sizes: {random_sizes}"
            ))

        self.stdout.write(self.style.SUCCESS(f"\n🎉 Total variants updated: {total_updated}"))
