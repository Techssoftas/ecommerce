import requests
from django.conf import settings
import logging

# logger = logging.getLogger(__name__)

DELHIVERY_PINCODE_URL = "https://track.delhivery.com/c/api/pin-codes/json/"

def check_delhivery_serviceability(pincode: str) -> bool:
    """
    Delhivery LIVE Pincode Serviceability check.
    Returns True if pincode is serviceable, False otherwise.
    """
    try:
        headers = {
            "Authorization": f"Token {settings.DELHIVERY_API_TOKEN}"
        }
        params = {
            "filter_codes": pincode
        }

        response = requests.get(
            DELHIVERY_PINCODE_URL,
            headers=headers,
            params=params,
            timeout=5.0
        )
        response.raise_for_status()  # Raise exception for 4xx/5xx status codes

        data = response.json()
        delivery_codes = data.get("delivery_codes", [])

        if not delivery_codes:
            # logger.warning(f"No delivery codes found for pincode: {pincode}")
            return False

        postal_code = delivery_codes[0].get("postal_code", {})
        remarks = (postal_code.get("remarks") or "").strip()

        if remarks.lower() == "embargo":
            # logger.info(f"Pincode {pincode} is under embargo")
            return False

        return True

    except requests.exceptions.RequestException as e:
        # logger.error(f"Delhivery request error for pincode {pincode}: {e}")
        return False
    except Exception as e:
        # logger.error(f"Delhivery unexpected error for pincode {pincode}: {e}", exc_info=True)
        return False