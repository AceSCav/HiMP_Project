from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User, Permission
from django.db import IntegrityError
from django.test import TestCase

from .models import AuditEvent, Cliente, Pagamento


class InstallmentTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser('admin', password='Local-test-2026!')
        self.person = Cliente.objects.create(nome_completo='Cliente parcelado')
        self.other = Cliente.objects.create(nome_completo='Outro cliente')
        self.client.force_login(self.user)
        self.url = f'/gestao/pagamentos/novo/?cliente={self.person.pk}'
        self.data = {'cliente': self.other.pk, 'montante': '1000.00', 'numero_parcelas': '3',
                     'data_limite': '2026-01-31', 'entidade': '00012', 'referencia': '00012345'}

    def payments(self):
        return list(Pagamento.objects.order_by('numero_parcela'))

    def test_optional_interval_creates_only_first_due_date_and_exact_total(self):
        response = self.client.post(self.url, self.data)
        self.assertRedirects(response, f'/gestao/pagamentos/?cliente={self.person.pk}')
        payments = self.payments()
        self.assertEqual([p.montante for p in payments], [Decimal('333.34'), Decimal('333.33'), Decimal('333.33')])
        self.assertEqual(sum(p.montante for p in payments), Decimal('1000'))
        self.assertEqual([p.data_limite for p in payments], [date(2026, 1, 31), None, None])
        self.assertEqual({p.cliente_id for p in payments}, {self.person.pk})
        self.assertEqual(len({p.plano_id for p in payments}), 1)
        self.assertEqual([p.numero_parcela for p in payments], [1, 2, 3])
        self.assertTrue(all(p.total_parcelas == 3 and p.referencia == '00012345' and p.entidade == '00012' and p.data_conclusao is None for p in payments))
        self.assertEqual(AuditEvent.objects.filter(action='add', model='office.Pagamento').count(), 3)
        self.assertContains(self.client.get(response.url), '1 de 3')

    def test_interval_means_exact_days_and_handles_year_leap_boundaries(self):
        data = {**self.data, 'data_limite': '2024-01-31', 'intervalo_dias': '30'}
        self.client.post(self.url, data)
        self.assertEqual([p.data_limite for p in self.payments()], [date(2024, 1, 31), date(2024, 3, 1), date(2024, 3, 31)])

    def test_validation_never_creates_partial_plans(self):
        invalid = [({'data_limite': ''}, 'data_limite'), ({'numero_parcelas': '0'}, 'numero_parcelas'),
            ({'numero_parcelas': '121'}, 'numero_parcelas'), ({'montante': '0.02'}, 'montante'),
            ({'intervalo_dias': '0'}, 'intervalo_dias'), ({'intervalo_dias': '-30'}, 'intervalo_dias'),
            ({'intervalo_dias': '1.5'}, 'intervalo_dias'), ({'data_limite': '9999-12-31', 'intervalo_dias': '30'}, 'intervalo_dias'),
            ({'data_conclusao': '2026-01-31'}, 'data_conclusao')]
        for changes, field in invalid:
            with self.subTest(changes=changes):
                response = self.client.post(self.url, {**self.data, **changes})
                self.assertEqual(response.status_code, 200)
                self.assertIn(field, response.context['form'].errors)
                self.assertEqual(Pagamento.objects.count(), 0)
                self.assertEqual(AuditEvent.objects.count(), 0)

    def test_single_payment_remains_compatible(self):
        self.client.post(self.url, {'montante': '19.99', 'data_conclusao': '2026-01-01'})
        payment = Pagamento.objects.get()
        self.assertEqual(payment.montante, Decimal('19.99'))
        self.assertIsNone(payment.plano_id)
        self.assertIsNone(payment.data_limite)
        self.assertEqual(payment.data_conclusao, date(2026, 1, 1))

    def test_later_due_dates_and_completion_can_be_edited_without_changing_siblings(self):
        self.client.post(self.url, self.data)
        first, second, third = self.payments()
        response = self.client.post(f'/gestao/pagamentos/{second.pk}/editar/',
            {'cliente': self.other.pk, 'montante': '333.33', 'data_limite': '2026-05-15', 'data_conclusao': '2026-05-14'})
        self.assertEqual(response.status_code, 302)
        second.refresh_from_db()
        first.refresh_from_db()
        third.refresh_from_db()
        self.assertEqual(second.cliente_id, self.person.pk)
        self.assertEqual(second.data_limite, date(2026, 5, 15))
        self.assertEqual(second.data_conclusao, date(2026, 5, 14))
        self.assertEqual(first.data_limite, date(2026, 1, 31))
        self.assertIsNone(third.data_limite)
        self.assertEqual(Pagamento.objects.count(), 3)
        self.assertContains(self.client.get(f'/gestao/pagamentos/{second.pk}/'), 'Outras parcelas do plano')

    def test_first_installment_cannot_lose_due_date(self):
        self.client.post(self.url, self.data)
        first = self.payments()[0]
        response = self.client.post(f'/gestao/pagamentos/{first.pk}/editar/', {'montante': '333.34', 'data_limite': ''})
        self.assertEqual(response.status_code, 200)
        self.assertIn('data_limite', response.context['form'].errors)
        first.refresh_from_db()
        self.assertEqual(first.data_limite, date(2026, 1, 31))

    def test_transaction_rolls_back_whole_plan_and_audit_on_failure(self):
        original = Pagamento.objects.create
        def create(**kwargs):
            if kwargs.get('numero_parcela') == 2:
                raise IntegrityError('simulated database failure')
            return original(**kwargs)
        with patch('office.payment_installments.Pagamento.objects.create', side_effect=create):
            response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Pagamento.objects.count(), 0)
        self.assertEqual(AuditEvent.objects.count(), 0)

    def test_viewer_cannot_create_installments(self):
        viewer = User.objects.create_user('viewer')
        viewer.user_permissions.add(Permission.objects.get(codename='view_pagamento'))
        self.client.force_login(viewer)
        self.assertEqual(self.client.post(self.url, self.data).status_code, 403)
        self.assertEqual(Pagamento.objects.count(), 0)
