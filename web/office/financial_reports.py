"""Payment reporting: receipt dates for revenue, due dates for receivables."""
from calendar import monthrange
from datetime import date
from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncMonth
from django.utils.formats import date_format, number_format

from .models import Pagamento

ZERO = Decimal('0.00')


def month_start(value, offset=0):
    index = value.year * 12 + value.month - 1 + offset
    year, month = divmod(index, 12)
    return date(year, month + 1, 1)


def preset_dates(period, today):
    last = today.replace(day=monthrange(today.year, today.month)[1])
    if period == 'mes':
        return today.replace(day=1), last
    if period == 'ano':
        return date(today.year, 1, 1), date(today.year, 12, 31)
    return month_start(today, -5), last


def money(value):
    return number_format(value, 2) + ' €'


def total(query):
    return query.aggregate(total=Sum('montante'))['total'] or ZERO


def build_report(start, end, today, client_id=None):
    base = Pagamento.objects.all()
    if client_id:
        base = base.filter(cliente_id=client_id)
    scope = Q(data_conclusao__range=(start, end)) | Q(data_conclusao__isnull=True, data_limite__range=(start, end))
    missing_amount = base.filter(scope, montante__isnull=True).count()
    invalid_amount = base.filter(scope, montante__lt=0).count()
    missing_dates = base.filter(data_conclusao__isnull=True, data_limite__isnull=True).count()
    valued = base.filter(montante__gte=0)
    received = valued.filter(data_conclusao__range=(start, end))
    expected = valued.filter(data_limite__range=(start, end))
    pending = expected.filter(data_conclusao__isnull=True)
    overdue = pending.filter(data_limite__lt=today)
    upcoming = pending.filter(data_limite__gte=today)
    received_total, pending_total, overdue_total = total(received), total(pending), total(overdue)
    expected_total = total(expected)
    received_months = {item['month'].date() if hasattr(item['month'], 'date') else item['month']: item['total'] for item in received.order_by().annotate(month=TruncMonth('data_conclusao')).values('month').annotate(total=Sum('montante'))}
    expected_months = {item['month'].date() if hasattr(item['month'], 'date') else item['month']: item['total'] for item in expected.order_by().annotate(month=TruncMonth('data_limite')).values('month').annotate(total=Sum('montante'))}
    months = []
    current = month_start(start)
    while current <= end:
        months.append({'date': current, 'label': date_format(current, 'M y'), 'received': received_months.get(current, ZERO), 'expected': expected_months.get(current, ZERO)})
        if current.year == end.year and current.month == end.month:
            break
        current = month_start(current, 1)
    maximum = max([v for m in months for v in (m['received'], m['expected'])] + [ZERO])
    # A round axis ceiling using Decimal throughout financial calculations.
    if maximum:
        step = Decimal(10) ** (maximum.adjusted() - 1)
        ceiling = ((maximum / (step * 5)).to_integral_value(rounding='ROUND_CEILING')) * step * 5
    else:
        ceiling = Decimal('100')
    width = max(720, len(months) * 84 + 100)
    chart_height, plot_height, top, left = 310, 220, 30, 75
    plot_width = width - left - 30
    group_width = plot_width / len(months)
    bar_width = min(24, group_width * .25)
    for index, month in enumerate(months):
        center = left + group_width * (index + .5)
        month.update({'x': round(center, 2), 'label': date_format(month['date'], 'M y')})
        month['bars'] = []
        for key, offset in [('received', -bar_width - 2), ('expected', 2)]:
            height = float(month[key] / ceiling) * plot_height
            month['bars'].append({'kind': key, 'x': round(center + offset, 2), 'y': round(top + plot_height - height, 2), 'height': round(height, 2), 'width': bar_width, 'amount': month[key]})
    ticks = [{'y': top + plot_height * (1 - i / 4), 'label': number_format(ceiling * i / 4, 0)} for i in range(5)]
    distribution = [
        {'label': 'Recebidos', 'kind': 'received', 'amount': received_total},
        {'label': 'Por receber · no prazo', 'kind': 'upcoming', 'amount': total(upcoming)},
        {'label': 'Por receber · em atraso', 'kind': 'overdue', 'amount': overdue_total},
    ]
    distribution_total = sum((item['amount'] for item in distribution), ZERO)
    offset = 0
    for item in distribution:
        percent = float(item['amount'] / distribution_total * 100) if distribution_total else 0
        item.update({'percent': round(percent, 1), 'length': round(percent, 5), 'offset': round(-offset, 5)})
        offset += percent
    breakdown = list(received.order_by().values('motivo__motivo').annotate(total=Sum('montante'), count=Count('pk')).order_by('-total', 'motivo__motivo'))
    categories = [{'label': item['motivo__motivo'] or 'Sem motivo definido', 'amount': item['total']} for item in breakdown[:5]]
    if len(breakdown) > 5:
        categories.append({'label': 'Outros motivos', 'amount': sum((item['total'] for item in breakdown[5:]), ZERO)})
    top_category = max([item['amount'] for item in categories] + [ZERO])
    for item in categories:
        item['width'] = round(float(item['amount'] / top_category * 100), 2) if top_category else 0
    aging = []
    from datetime import timedelta
    for label, lower, upper in [('Até 30 dias', 1, 30), ('31–60 dias', 31, 60), ('61–90 dias', 61, 90), ('Mais de 90 dias', 91, None)]:
        records = overdue.filter(data_limite__lte=today - timedelta(days=lower))
        if upper:
            records = records.filter(data_limite__gte=today - timedelta(days=upper))
        aging.append({'label': label, 'amount': total(records), 'count': records.count()})
    aging_max = max([item['amount'] for item in aging] + [ZERO])
    for item in aging:
        item['width'] = round(float(item['amount'] / aging_max * 100), 2) if aging_max else 0
    return {
        'received_total': received_total, 'pending_total': pending_total, 'overdue_total': overdue_total,
        'expected_total': expected_total, 'received_count': received.count(), 'pending_count': pending.count(),
        'overdue_count': overdue.count(), 'months': months, 'ticks': ticks,
        'chart_width': width, 'chart_height': chart_height, 'distribution': distribution,
        'distribution_total': distribution_total, 'categories': categories, 'aging': aging,
        'has_amounts': any(m['received'] or m['expected'] for m in months),
        'missing_amount': missing_amount, 'invalid_amount': invalid_amount, 'missing_dates': missing_dates,
    }
