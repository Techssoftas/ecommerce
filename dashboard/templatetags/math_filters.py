from django import template

register = template.Library()

def to_float(value):
    try:
        if value is None or value == '':
            return 0.0
        return float(str(value).strip())
    except (ValueError, TypeError):
        return 0.0

@register.filter
def mul(value, arg):
    return to_float(value) * to_float(arg)

@register.filter
def subtract(value, arg):
    return to_float(value) - to_float(arg)


@register.simple_tag
def get_total_gst(order_items):
    total = 0.0
    for item in order_items.items.all():
        price = to_float(item.size_variant.price)
        gst = price * 0.05
        total += gst
    return round(total, 2)