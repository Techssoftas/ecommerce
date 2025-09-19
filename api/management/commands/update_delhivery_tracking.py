from django.core.management.base import BaseCommand
from api.models import OrderTracking
from api.delhivery_utils import fetch_and_update_tracking

class Command(BaseCommand):
    help = "Fetch and update Delhivery tracking info"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING(">>> Command started <<<"))

        trackings = OrderTracking.objects.exclude(
            current_status__in=["Delivered", "RTO Delivered"]
        )
        self.stdout.write(self.style.WARNING(f"Trackings count: {trackings.count()}"))

        if not trackings.exists():
            self.stdout.write(self.style.NOTICE("No pending trackings found."))
            return

        for tracking in trackings:
            self.stdout.write(f"Processing AWB: {tracking.awb_number}")
            success, message = fetch_and_update_tracking(tracking.awb_number)
            self.stdout.write(self.style.SUCCESS(message) if success else self.style.ERROR(message))

        self.stdout.write(self.style.WARNING(">>> Command finished <<<"))
