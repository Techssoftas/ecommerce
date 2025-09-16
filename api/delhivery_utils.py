# your_app/delhivery_utils.py

import requests
from django.conf import settings
from api.models import OrderTracking, TrackingScan
from django.utils.dateparse import parse_datetime

def fetch_and_update_tracking(awb_number):
    url = f"https://track.delhivery.com/api/v1/packages/json/?waybill={awb_number}"
    headers = {
        "Authorization": f"Token {settings.DELHIVERY_API_TOKEN}"
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return False, f"Failed to fetch for {awb_number}"

    data = response.json()
    shipment_data = data.get("ShipmentData", [])[0].get("Shipment", {})

    try:
        tracking = OrderTracking.objects.get(awb_number=awb_number)
    except OrderTracking.DoesNotExist:
        return False, f"Tracking not found for {awb_number}"

    # Update current status
    current_status = shipment_data.get("Status", {}).get("Status")
    tracking.current_status = current_status
    tracking.raw_data = shipment_data
    tracking.save()

    # Parse scan events
    scan_events = shipment_data.get("Scans", [])
    for scan in scan_events:
        scan_id = scan.get("ScanType", "") + scan.get("ScanDatetime", "")
        if scan_id == tracking.last_event_id:
            continue  # Already processed this event

        # New scan
        TrackingScan.objects.create(
            tracking=tracking,
            status=scan.get("ScanType", ""),
            location=scan.get("ScannedLocation", ""),
            scan_time=parse_datetime(scan.get("ScanDatetime"))
        )

        tracking.last_event_id = scan_id
        tracking.save()

    return True, f"Updated {awb_number}"
