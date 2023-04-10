from django import template
register = template.Library()

@register.filter
def replace(value, arg):
    return value.replace(arg, "_V1_Ratio0.4_AL_.jpg")