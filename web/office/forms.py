import re
import zipfile
from datetime import date
from io import BytesIO

from django import forms
from django.core.exceptions import ValidationError
from django.db import models
from .models import Configuration, DocumentTemplate, Cliente


class RecordForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            model_field = self._meta.model._meta.get_field(name)
            if isinstance(model_field, models.DateTimeField):
                field.widget = forms.DateTimeInput(format='%Y-%m-%dT%H:%M', attrs={'type': 'datetime-local'})
            elif isinstance(model_field, models.DateField):
                field.widget = forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'})
            elif isinstance(field.widget, forms.Textarea):
                if name in ('notas_documento', 'observacao', 'descricao'):
                    field.widget.attrs['rows'] = 4
                else:
                    field.widget = forms.TextInput()
            if isinstance(field, forms.CharField):
                field.max_length = field.max_length or 2000
        categories = {
            'estado_civil': Configuration.Category.MARITAL, 'genero': Configuration.Category.GENDER,
            'duracao': Configuration.Category.DURATION, 'motivo': Configuration.Category.REASON,
            'documento_nome': Configuration.Category.DOCUMENT,
        }
        for name, category in categories.items():
            # Pagamento.motivo is an existing foreign key, not a text catalogue.
            if name not in self.fields or not isinstance(self._meta.model._meta.get_field(name), models.TextField):
                continue
            labels = list(Configuration.objects.filter(category=category, active=True).values_list('label', flat=True))
            old = getattr(self.instance, name, None)
            if old and old not in labels:
                labels.append(old)  # Preserve inactive/historical values when editing.
            self.fields[name] = forms.ChoiceField(
                label=self.fields[name].label, required=self.fields[name].required,
                choices=[('', 'Selecione…')] + [(v, v) for v in labels],
            )
        for name in ('nome_completo', 'titulo', 'cliente', 'documento_nome', 'processo', 'montante', 'data_inicio', 'duracao'):
            if name in self.fields:
                self.fields[name].required = True

    def clean(self):
        data = super().clean()
        # Unique optional identifiers must be NULL, not an empty unique string.
        for name in ('nif', 'niss', 'passaporte', 'titulo_residencia', 'numero_processo'):
            if name in data and not data[name]:
                data[name] = None
        for name, length in [('nif', 9), ('niss', 11)]:
            value = data.get(name)
            if value and not re.fullmatch(rf'[0-9]{{{length}}}', value):
                self.add_error(name, f'Introduza {length} algarismos.')
        if data.get('montante') is not None and data['montante'] < 0:
            self.add_error('montante', 'O montante não pode ser negativo.')
        if data.get('data_nascimento') and data['data_nascimento'] > date.today():
            self.add_error('data_nascimento', 'A data de nascimento não pode ser futura.')
        for start, end in [('emissao_passaporte', 'validade_passaporte'), ('emissao_bi_cc', 'validade_bi_cc')]:
            if data.get(start) and data.get(end) and data[start] > data[end]:
                self.add_error(end, 'A validade deve ser posterior à emissão.')
        return data


def record_form(resource):
    return forms.modelform_factory(resource.model, form=RecordForm, fields=resource.fields)


class TemplateAdminForm(forms.ModelForm):
    class Meta:
        model = DocumentTemplate
        fields = '__all__'

    def clean_required_fields(self):
        fields = self.cleaned_data['required_fields']
        if not isinstance(fields, list) or len(fields) > 100 or any(
            not isinstance(f, str) or not re.fullmatch(r'[\w]{1,80}', f) for f in fields
        ):
            raise ValidationError('Use uma lista JSON de nomes de campos simples (máximo 100).')
        return fields

    def clean_file(self):
        file = self.cleaned_data['file']
        if not file.name.lower().endswith('.docx') or file.size > 5 * 1024 * 1024:
            raise ValidationError('Envie um DOCX com até 5 MB.')
        try:
            file.open('rb')
            with zipfile.ZipFile(BytesIO(file.read())) as archive:
                members = archive.infolist()
                if sum(m.file_size for m in members) > 25 * 1024 * 1024:
                    raise ValidationError('O conteúdo descomprimido excede o limite.')
                if 'word/document.xml' not in archive.namelist() or any('vbaProject' in m.filename for m in members):
                    raise ValidationError('O ficheiro não é um DOCX válido sem macros.')
        except (zipfile.BadZipFile, OSError):
            raise ValidationError('O ficheiro DOCX está danificado.')
        finally:
            file.seek(0)
        return file


class GenerationForm(forms.Form):
    cliente = forms.ModelChoiceField(queryset=Cliente.objects.all(), label='Cliente')
    modelo = forms.ModelChoiceField(queryset=DocumentTemplate.objects.filter(active=True), label='Modelo')
    valor_contrato = forms.DecimalField(label='Valor do contrato (€)', max_digits=12, decimal_places=2, min_value=0, required=False)
    numero_parcelas = forms.IntegerField(label='Número de prestações', min_value=1, max_value=120, required=False)
    inicio_prestacao = forms.DateField(label='Início das prestações', widget=forms.DateInput(attrs={'type': 'date'}), required=False)
