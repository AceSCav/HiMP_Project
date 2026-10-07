from datetime import date, datetime
from decimal import Decimal
from django import template
from django.utils.formats import date_format, number_format
from django.utils import timezone

register = template.Library()

@register.filter
def display_value(value):
    if value is None or value == '':
        return '—'
    if isinstance(value, bool):
        return 'Sim' if value else 'Não'
    if isinstance(value, datetime):
        return date_format(timezone.localtime(value), 'd/m/Y H:i')
    if isinstance(value, date):
        return date_format(value, 'd/m/Y')
    if isinstance(value, Decimal):
        return number_format(value, 2) + ' €'
    return str(value)

@register.simple_tag(takes_context=True)
def page_query(context, number):
    params = context['request'].GET.copy()
    params['page'] = number
    return params.urlencode()
