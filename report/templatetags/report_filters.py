from django import template

register = template.Library()

@register.filter
def get_range(value):
    """Create a range from 1 to value"""
    try:
        if value and int(value) > 0:
            return range(1, int(value) + 1)
        return range(0)
    except (ValueError, TypeError):
        return range(0)

@register.filter
def multiply(value, arg):
    """Multiply the value by the argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def divisibleby(value, arg):
    """Divide value by arg"""
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def percentage(value, total):
    """Calculate percentage"""
    try:
        return (float(value) / float(total)) * 100
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def get_item(dictionary, key):
    """Get item from dictionary"""
    return dictionary.get(key, '')

@register.filter
def sum_attr(queryset, attr):
    """Sum a specific attribute from a list of dictionaries"""
    try:
        return sum(item.get(attr, 0) for item in queryset)
    except (AttributeError, TypeError):
        return 0

@register.filter
def to_json(value):
    """Convert value to JSON string"""
    import json
    return json.dumps(value)

@register.filter
def div(value, arg):
    """Divide value by arg"""
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0
    

@register.filter
def divide(value, arg):
    """Safely divide the value by the argument"""
    try:
        if float(arg) == 0:
            return 0
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError, TypeError):
        return 0


@register.filter
def subtract(value, arg):
    """Safely subtract the argument from the value"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0
    


@register.filter
def mul(value, arg):
    """Multiply value by arg."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0
    

@register.filter
def abs(value):
    """Return absolute value."""
    try:
        return abs(float(value))
    except (ValueError, TypeError):
        return value