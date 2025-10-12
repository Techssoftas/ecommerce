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
def get_total_gst(order_items, cod_charge=None):
    total = 0.0
    for item in order_items.items.all():
        price = to_float(item.size_variant.price)
        gst = price * 0.05
        total += gst

    # add COD GST if present
    if cod_charge:
        total += to_float(cod_charge.get("gst_amount", 0))
    return round(total, 2)
