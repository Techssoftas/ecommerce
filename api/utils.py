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
