# utils.py
from datetime import timedelta
from django.utils import timezone

def get_delivered_time(order_item):
    # prefer explicit delivered_at on order_item/order; fallback to order.updated_at if status delivered
    if hasattr(order_item, 'delivered_at') and order_item.delivered_at:
        return order_item.delivered_at
    order = order_item.order
    if order.status == 'Delivered':
        return order.updated_at
    return None

def is_within_return_window(order_item, request_time=None):
    request_time = request_time or timezone.now()
    delivered = get_delivered_time(order_item)
    if not delivered:
        return False, "Item not delivered yet"
    period_days = order_item.product.return_period or 0
    deadline = delivered + timedelta(days=period_days)
    if request_time <= deadline:
        return True, ""
    return False, f"Return window expired on {deadline}"



import requests
from django.conf import settings

def send_sms(mobile, template_id, variables):
    try:
        url = "https://api.msg91.com/api/v5/flow/"  # Flow API URL

        payload = {
            "flow_id": template_id,
            "sender": 'MTEXTE',
            "short_url": "1",
            "recipients": [
                {
                    "mobiles": str(mobile),
                    **variables
                }
            ]
        }

        headers = {
            "accept": "application/json",
            "authkey": settings.MSG91_API_KEY,
            "Content-Type": "application/json"
        }

        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # error throw panna use pannum

        print("✅ SMS sent successfully:", response.text)
        return True

    except requests.exceptions.RequestException as e:
        print("⚠️ SMS sending failed:", e)
        return False



import requests
import logging

logger = logging.getLogger(__name__)

MSG91_FLOW_URL = "https://control.msg91.com/api/v5/flow"


def _normalize_mobile(mobile: str) -> str:
    """Ensure mobile number is in correct 91XXXXXXXXXX format."""
    if not mobile:
        return mobile
    m = ''.join(ch for ch in str(mobile).strip() if ch.isdigit())
    if len(m) == 10:
        return "91" + m
    if len(m) == 11 and m.startswith("0"):
        return "91" + m[1:]
    return m


def send_order_sms(authkey: str, template_id: str, mobile: str, name: str, order_id: str) -> dict:
    """
    Send order confirmation SMS to a single user.
    Template: Dear ##name##, Your order ##id## has been Successfully placed on MTEX. Thank you for shopping with us!
    So -> VAR1 = name, VAR2 = order_id
    """
    try:
        normalized_mobile = _normalize_mobile(mobile)

        payload = {
            "template_id": template_id,
            "short_url": "0",
            "recipients": [
                {
                    "mobiles": normalized_mobile,
                    "name": name,
                    "id": order_id
                }
            ]
        }

        headers = {
            "accept": "application/json",
            "authkey": authkey,
            "content-type": "application/json"
        }

        response = requests.post(MSG91_FLOW_URL, json=payload, headers=headers, timeout=10)

        try:
            data = response.json()
        except Exception:
            data = {"status_code": response.status_code, "text": response.text}

        if response.status_code in [200, 201]:
            logger.info(f"SMS sent successfully to {normalized_mobile}")
            return {"success": True, "detail": "SMS sent successfully", "raw_response": data}
        else:
            logger.warning(f"MSG91 send failed: {data}")
            return {"success": False, "detail": "MSG91 send failed", "raw_response": data}

    except Exception as e:
        logger.exception("SMS send exception")
        return {"success": False, "detail": str(e), "raw_response": None}
