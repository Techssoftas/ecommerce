import json
import requests
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = "Test Delhivery Pickup Request Creation API"

    def handle(self, *args, **options):
        token = 'd7c1fdb1b8ca98d9fd3fc884a771fd4e96ffaf1e'
        pickup_url =  "https://track.delhivery.com/fm/request/new/"  # TESTING URL

        # next day 2pm
        pickup_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        pickup_time = "14:00:00"

        payload = {
            "pickup_time": pickup_time,
            "pickup_date": pickup_date,
            "pickup_location": "M Tex",  # must match registered warehouse
            "expected_package_count": 1
        }

        headers = {
            "Authorization": f"Token {token}",
            "Content-Type": "application/json"
        }

        self.stdout.write("Sending pickup request...")
        resp = requests.post(pickup_url, json=payload, headers=headers, timeout=30)
        self.stdout.write(f"Status: {resp.status_code}")
        
        try:
            data = resp.json()
        except Exception:
            data = {"raw_text": resp.text}

        self.stdout.write(json.dumps(data, indent=2))
