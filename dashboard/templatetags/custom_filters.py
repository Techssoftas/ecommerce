
from django import template
from datetime import timedelta

register = template.Library()

@register.filter
def add_days(value, days):
    try:
        return value + timedelta(days=int(days))
    except:
        return value



# Global master list – inga maintain pannunga
ALL_SIZES = ["XXS","XS","S","M","L","XL","XXL","XXXL","4XL","5XL"]

@register.simple_tag
def all_sizes():
    """Return master list of sizes."""
    return ALL_SIZES

@register.simple_tag
def existing_size_names(variant):
    """Return ['S','M',...] from variant without calling in template."""
    return list(variant.sizes.values_list("size", flat=True))

@register.simple_tag
def remaining_sizes(variant):
    """Return sizes not yet present in this variant."""
    used = set(variant.sizes.values_list("size", flat=True))
    return [s for s in ALL_SIZES if s not in used]