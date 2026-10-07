from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

from .models import Pagamento


def create_installments(form):
    """Called inside the view transaction, after validating the creation form."""
    data = form.cleaned_data
    count = data['numero_parcelas']
    if count == 1:
        return [form.save()]
    # Work in integer cents; distribute the remainder over the first parcels.
    cents, remainder = divmod(int(data['montante'] * 100), count)
    plan = uuid4()
    payments = []
    for index in range(count):
        due = data['data_limite'] if index == 0 else None
        if data.get('intervalo_dias'):
            due = data['data_limite'] + timedelta(days=index * data['intervalo_dias'])
        payments.append(Pagamento.objects.create(
            cliente=data['cliente'], entidade=data.get('entidade'), referencia=data.get('referencia'),
            motivo=data.get('motivo'), status=data.get('status'),
            montante=Decimal(cents + (1 if index < remainder else 0)) / 100,
            data_limite=due, data_conclusao=None, plano_id=plan,
            numero_parcela=index + 1, total_parcelas=count,
        ))
    return payments
