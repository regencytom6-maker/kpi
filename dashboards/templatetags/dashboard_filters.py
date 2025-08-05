"""
Custom template filters for dashboard templates
"""
from django import template

register = template.Library()

@register.filter
def nice_phase_name(value):
    """Convert phase_name with underscores to readable format"""
    if value:
        # Replace underscores with spaces
        value = value.replace("_", " ")
        # Capitalize each word
        return value.title()
    return value
