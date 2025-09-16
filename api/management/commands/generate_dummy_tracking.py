import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from api.models import Order, OrderTracking, TrackingScan


DUMMY_STATUSES = [
    ("Shipment Created", "Chennai"),
    ("Picked Up", "Chennai"),
    ("In Transit", "Bangalore"),
    ("Out for Delivery", "Bangalore"),
    ("Delivered", "Bangalore"),
]


class Command(BaseCommand):
    help = "Generate dummy tracking and scan data for existing orders"

    def handle(self, *args, **kwargs):
        orders = Order.objects.all()[:4]  # First 4 orders

        if not orders:
            self.stdout.write(self.style.ERROR("No orders found in DB"))
            return

        for order in orders:
            awb = f"TESTAWB{order.id:04d}"

            tracking, created = OrderTracking.objects.get_or_create(
                order=order,
                defaults={
                    "awb_number": awb,
                    "current_status": "Shipment Created",
                    "last_event_id": "",
                    "raw_data": {},
                }
            )

            self.stdout.write(f"{'Created' if created else 'Updated'} tracking for Order #{order.id} | AWB: {awb}")

            # Clear previous scans
            tracking.scans.all().delete()

            # Add dummy scans
            base_time = timezone.now() - timezone.timedelta(days=4)
            for i, (status, location) in enumerate(DUMMY_STATUSES):
                scan_time = base_time + timezone.timedelta(hours=i * 8)
                TrackingScan.objects.create(
                    tracking=tracking,
                    status=status,
                    location=location,
                    scan_time=scan_time
                )

            tracking.current_status = DUMMY_STATUSES[-1][0]
            tracking.last_event_id = f"{DUMMY_STATUSES[-1][0]}{scan_time.isoformat()}"
            tracking.save()

        self.stdout.write(self.style.SUCCESS("✅ Dummy tracking and scan data generated."))
