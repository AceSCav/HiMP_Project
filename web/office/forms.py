import re
import zipfile
from copy import deepcopy
from datetime import date, timedelta
from io import BytesIO

from django import forms
from django.core.exceptions import ValidationError
from django.db import models
from .models import Configuration, DocumentTemplate, Cliente, DocumentoCliente, Pagamento


def validate_drive_file(file):
    if file.size > 10 * 1024 * 1024 or file.size == 0:
        raise ValidationError('Envie um ficheiro com até 10 MB, não vazio.')
    suffix = file.name.lower().rsplit('.', 1)[-1]
    file.seek(0)
    head = file.read(8)
    file.seek(0)
    valid = (suffix == 'pdf' and head.startswith(b'%PDF-') or
             suffix == 'png' and head.startswith(b'\x89PNG\r\n\x1a\n') or
             suffix in ('jpg', 'jpeg') and head.startswith(b'\xff\xd8\xff'))
    if suffix == 'docx':
        try:
            with zipfile.ZipFile(file) as archive:
                valid = ('word/document.xml' in archive.namelist() and
                         sum(m.file_size for m in archive.infolist()) <= 50 * 1024 * 1024 and
                         not any('vbaproject' in m.filename.lower() for m in archive.infolist()))
        except (zipfile.BadZipFile, OSError):
            valid = False
        finally:
            file.seek(0)
    if not valid:
        raise ValidationError('Use PDF, DOCX sem macros, JPG ou PNG válidos.')


class DriveUploadForm(forms.Form):
    ficheiro = forms.FileField(label='Ficheiro para guardar no Google Drive', validators=[validate_drive_file],
                              help_text='PDF, DOCX, JPG ou PNG · até 10 MB.')


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
        if self._meta.model == DocumentoCliente and not self.instance.drive_file_id:
            self.fields['ficheiro'] = deepcopy(DriveUploadForm.base_fields['ficheiro'])
            self.fields['ficheiro'].required = False
            self.fields['ficheiro'].help_text += ' Opcional; requer ligação Google do escritório.'
        if self._meta.model == Pagamento and not self.instance.pk:
            self.fields['montante'].label = 'Valor total (€)'
            self.fields['montante'].help_text = 'O valor será dividido pelas parcelas, com acerto dos cêntimos para manter o total.'
            self.fields['numero_parcelas'] = forms.IntegerField(label='Número de parcelas', min_value=1, max_value=120, initial=1, required=False,
                help_text='Use 1 para pagamento único. Pode criar até 120 parcelas de uma vez.')
            self.fields['intervalo_dias'] = forms.IntegerField(label='Intervalo entre parcelas (dias)', min_value=1, max_value=365, required=False,
                widget=forms.NumberInput(attrs={'placeholder': 'Opcional · exemplo: 30'}),
                help_text='Em branco: só a primeira tem vencimento; as restantes ficam sem data. Ex.: 30 cria vencimentos a cada 30 dias.')
            self.fields['data_limite'].label = 'Data limite da primeira parcela'
            self.fields['data_limite'].help_text = 'Obrigatória quando existem várias parcelas. As restantes datas podem ser definidas individualmente depois.'
            self.fields['data_conclusao'].help_text = 'Para pagamento parcelado, registe a conclusão de cada parcela depois de criar o plano.'
            self.fields['status'].help_text = 'Estado inicial aplicado a todas as parcelas.'
            self.fields['referencia'].help_text = 'Aplicada a todas as parcelas; pode alterar a referência de cada uma depois.'
            self.order_fields(['cliente', 'montante', 'numero_parcelas', 'data_limite', 'intervalo_dias', 'entidade', 'referencia', 'motivo', 'status', 'data_conclusao'])
        elif self._meta.model == Pagamento and self.instance.numero_parcela == 1:
            self.fields['data_limite'].required = True
            self.fields['data_limite'].help_text = 'A primeira parcela do plano tem de manter uma data limite.'

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
        if self._meta.model == Pagamento and not self.instance.pk:
            count = data.get('numero_parcelas') or 1
            data['numero_parcelas'] = count
            if count > 1:
                if not data.get('data_limite'):
                    self.add_error('data_limite', 'Defina a data limite da primeira parcela.')
                if data.get('montante') is not None and data['montante'] * 100 < count:
                    self.add_error('montante', 'O total deve permitir pelo menos 0,01 € por parcela.')
                if data.get('data_conclusao'):
                    self.add_error('data_conclusao', 'Registe a conclusão de cada parcela individualmente, depois de criar o plano.')
                if data.get('data_limite') and data.get('intervalo_dias'):
                    try:
                        data['data_limite'] + timedelta(days=data['intervalo_dias'] * (count - 1))
                    except OverflowError:
                        self.add_error('intervalo_dias', 'O último vencimento ultrapassa o limite de datas. Reduza o intervalo ou o número de parcelas.')
            elif data.get('intervalo_dias'):
                self.add_error('intervalo_dias', 'O intervalo só é usado quando existem várias parcelas.')
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
    guardar_drive = forms.BooleanField(label='Guardar na pasta Google Drive do cliente', required=False)
    valor_contrato = forms.DecimalField(label='Valor do contrato (€)', max_digits=12, decimal_places=2, min_value=0, required=False)
    numero_parcelas = forms.IntegerField(label='Número de prestações', min_value=1, max_value=120, required=False)
    inicio_prestacao = forms.DateField(label='Início das prestações', widget=forms.DateInput(attrs={'type': 'date'}), required=False)
