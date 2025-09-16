from django.core.management.base import BaseCommand
from api.models import OrderTracking
from api.delhivery_utils import fetch_and_update_tracking

class Command(BaseCommand):
    help = "Fetch and update Delhivery tracking info"

    def handle(self, *args, **kwargs):
        trackings = OrderTracking.objects.exclude(current_status__in=["Delivered", "RTO Delivered"])

        for tracking in trackings:
            success, message = fetch_and_update_tracking(tracking.awb_number)
            self.stdout.write(self.style.SUCCESS(message) if success else self.style.ERROR(message))
