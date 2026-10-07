from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User, Permission
from django.test import TestCase, override_settings

from .financial_reports import build_report, preset_dates
from .models import Cliente, Motivo, Pagamento


@override_settings(STORAGES={'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'}, 'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'}})
class FinancialReportTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('relatorios', password='Senha-para-testes-2026!')
        self.user.user_permissions.add(Permission.objects.get(content_type__app_label='office', codename='view_pagamento'))
        self.person = Cliente.objects.create(nome_completo='Cliente dos relatórios')
        self.client.force_login(self.user)
        self.start, self.end, self.today = date(2026, 10, 1), date(2026, 10, 31), date(2026, 10, 7)

    def payment(self, amount, due=None, completed=None, **kwargs):
        return Pagamento.objects.create(cliente=self.person, montante=amount, data_limite=due, data_conclusao=completed, **kwargs)

    def test_receipt_date_and_due_date_have_distinct_meanings(self):
        self.payment(Decimal('25.10'), date(2026, 9, 15), date(2026, 10, 2))
        self.payment(Decimal('100'), date(2026, 10, 10), date(2026, 9, 20))
        self.payment(Decimal('19.99'), date(2026, 10, 1))
        self.payment(Decimal('80'), date(2026, 10, 7))
        self.payment(Decimal('500'), date(2026, 11, 1))
        report = build_report(self.start, self.end, self.today)
        self.assertEqual(report['received_total'], Decimal('25.10'))
        self.assertEqual(report['pending_total'], Decimal('99.99'))
        self.assertEqual(report['overdue_total'], Decimal('19.99'))
        self.assertEqual(report['expected_total'], Decimal('199.99'))
        self.assertEqual(report['distribution_total'], Decimal('125.09'))
        self.assertEqual(report['months'][0]['received'], Decimal('25.10'))
        self.assertEqual(report['months'][0]['expected'], Decimal('199.99'))

    def test_client_filter_is_applied_to_all_totals(self):
        other = Cliente.objects.create(nome_completo='Outro cliente')
        self.payment(Decimal('20'), date(2026, 10, 2))
        Pagamento.objects.create(cliente=other, montante=Decimal('1000'), data_limite=date(2026, 10, 2))
        report = build_report(self.start, self.end, self.today, self.person.pk)
        self.assertEqual(report['pending_total'], Decimal('20'))
        response = self.client.get('/relatorios/financeiro/', {'inicio': '2026-10-01', 'fim': '2026-10-31', 'cliente': self.person.pk})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['report']['pending_total'], Decimal('20'))

    def test_empty_report_and_month_gaps_are_safe(self):
        self.payment(Decimal('10'), completed=date(2026, 7, 1))
        report = build_report(date(2026, 5, 1), self.end, self.today)
        self.assertEqual(len(report['months']), 6)
        self.assertEqual(report['months'][0]['received'], Decimal('0'))
        self.assertEqual(report['months'][2]['received'], Decimal('10'))
        empty = build_report(self.start, self.end, self.today)
        self.assertFalse(empty['has_amounts'])
        self.assertEqual(empty['distribution_total'], Decimal('0'))
        self.assertEqual(self.client.get('/relatorios/financeiro/').status_code, 200)

    def test_dates_invalid_partial_reversed_and_excessive_rejected(self):
        for query in [
            {'inicio': 'invalid', 'fim': '2026-10-31'},
            {'inicio': '2026-10-01'},
            {'inicio': '2026-11-01', 'fim': '2026-10-31'},
            {'inicio': '2020-01-01', 'fim': '2026-10-31'},
            {'inicio': '2026-10-01', 'fim': '2026-10-31', 'cliente': '999999'},
        ]:
            with self.subTest(query=query), patch('office.financial_reports.build_report') as builder:
                response = self.client.get('/relatorios/financeiro/', query)
                self.assertEqual(response.status_code, 200)
                self.assertIsNone(response.context['report'])
                self.assertTrue(response.context['form'].errors)
                builder.assert_not_called()

    def test_unauthorized_access_and_navigation(self):
        self.client.logout()
        self.assertEqual(self.client.get('/relatorios/financeiro/').status_code, 302)
        user = User.objects.create_user('sem-financas', password='Senha-para-testes-2026!')
        self.client.force_login(user)
        self.assertEqual(self.client.get('/relatorios/financeiro/').status_code, 403)
        self.assertNotContains(self.client.get('/'), 'href="/relatorios/financeiro/"')
        self.client.force_login(self.user)
        self.assertContains(self.client.get('/'), 'href="/relatorios/financeiro/"')

    def test_aging_bucket_boundaries(self):
        from datetime import timedelta
        for days in [1, 30, 31, 60, 61, 90, 91]:
            self.payment(Decimal('10'), self.today - timedelta(days=days))
        report = build_report(date(2026, 1, 1), self.end, self.today)
        self.assertEqual([item['count'] for item in report['aging']], [2, 2, 2, 1])
        self.assertEqual(sum((item['amount'] for item in report['aging']), Decimal('0')), report['overdue_total'])

    def test_missing_dates_and_amounts_explained_without_inventing_revenue(self):
        self.payment(None, date(2026, 10, 2))
        self.payment(Decimal('90'))
        self.payment(Decimal('-10'), date(2026, 10, 2))
        report = build_report(self.start, self.end, self.today)
        self.assertEqual(report['missing_amount'], 1)
        self.assertEqual(report['missing_dates'], 1)
        self.assertEqual(report['invalid_amount'], 1)
        self.assertEqual(report['received_total'], Decimal('0'))
        self.assertEqual(report['pending_total'], Decimal('0'))

    def test_category_totals_and_escaping(self):
        for index in range(7):
            reason = Motivo.objects.create(motivo=f'Motivo {index}')
            self.payment(Decimal(index + 1), completed=date(2026, 10, 2), motivo=reason)
        malicious = Motivo.objects.create(motivo='<script>alert(1)</script>')
        self.payment(Decimal('99'), completed=date(2026, 10, 3), motivo=malicious)
        report = build_report(self.start, self.end, self.today)
        self.assertEqual(len(report['categories']), 6)
        self.assertEqual(sum((item['amount'] for item in report['categories']), Decimal('0')), report['received_total'])
        response = self.client.get('/relatorios/financeiro/', {'inicio': '2026-10-01', 'fim': '2026-10-31'})
        self.assertNotContains(response, '<script>alert(1)</script>')
        self.assertContains(response, '&lt;script&gt;alert(1)&lt;/script&gt;')
        self.assertEqual(response['Cache-Control'], 'no-store, private')

    def test_presets_use_calendar_boundaries(self):
        self.assertEqual(preset_dates('mes', date(2024, 2, 15)), (date(2024, 2, 1), date(2024, 2, 29)))
        self.assertEqual(preset_dates('6m', date(2026, 1, 4)), (date(2025, 8, 1), date(2026, 1, 31)))
        self.assertEqual(preset_dates('ano', self.today), (date(2026, 1, 1), date(2026, 12, 31)))
