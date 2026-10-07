from django import forms
from .models import Cliente


class FinancialReportForm(forms.Form):
    inicio = forms.DateField(label='De', widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}))
    fim = forms.DateField(label='Até', widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}))
    cliente = forms.ModelChoiceField(label='Cliente', queryset=Cliente.objects.all(), required=False, empty_label='Todos os clientes')

    def clean(self):
        data = super().clean()
        start, end = data.get('inicio'), data.get('fim')
        if start and end:
            if start > end:
                self.add_error('fim', 'A data final deve ser igual ou posterior à data inicial.')
            elif (end.year - start.year) * 12 + end.month - start.month >= 36:
                self.add_error('fim', 'Escolha um período de até 36 meses.')
        return data
