import requests
from django.conf import settings
import logging
logger = logging.getLogger('dashboard')
DELHIVERY_PINCODE_URL = "https://track.delhivery.com/c/api/pin-codes/json/"


def check_delhivery_serviceability(pincode: str) -> bool:
    """
    Delhivery B2C Pincode Serviceability check.
    Returns True if pincode is serviceable, False otherwise.
    """
    try:
        headers = {
            "Authorization": f"Token {settings.DELHIVERY_API_TOKEN}"  # settings.py la add pannunga
        }
        params = {
            "filter_codes": pincode
        }
        
        resp = requests.get(
            DELHIVERY_PINCODE_URL,
            headers=headers,
            params=params,
            timeout=5
        )

        resp.raise_for_status()
        data = resp.json()
        print(f"Delhivery serviceability response for {pincode}: {data}")
        logger.info(f"Delhivery serviceability response: {data}")
        delivery_codes = data.get("delivery_codes", [])

        # 1. Empty list => NSZ (non-serviceable)
        if not delivery_codes:
            return False

        postal_code = delivery_codes[0].get("postal_code", {})
        remarks = (postal_code.get("remarks") or "").strip()

        # 2. remarks == "Embargo" => temporary NSZ => non-serviceable
        if remarks.lower() == "embargo":
            return False

        # 3. remark blank => serviceable
        return True

    except Exception as e:
        # API error na safe side la non-serviceable nu treat pannalam
        print(f"Delhivery serviceability check error for {pincode}: {e}")
        return False
