from datetime import date
from decimal import Decimal
from functools import wraps
from io import BytesIO

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Q, Sum
from django.db.models.deletion import ProtectedError
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.formats import number_format
from django.views.decorators.http import require_POST

from .forms import GenerationForm, record_form
from .models import Agendamento, AuditEvent, Cliente, Configuration, DocumentoCliente, Pagamento, Processo
from .registry import RESOURCES


def resource_access(action):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(request, resource, *args, **kwargs):
            spec = RESOURCES.get(resource)
            if not spec:
                raise Http404
            if not request.user.has_perm(f'office.{action}_{spec.model._meta.model_name}'):
                raise PermissionDenied
            return view(request, resource, spec, *args, **kwargs)
        return wrapped
    return decorator


def audit(request, action, instance):
    AuditEvent.objects.create(actor=request.user, action=action, model=instance._meta.label, object_id=str(instance.pk))


def queryset(spec):
    related = [f.name for f in spec.model._meta.fields if f.is_relation]
    return spec.model.objects.select_related(*related)


@login_required
def dashboard(request):
    today = timezone.localdate()
    cards = []
    for key, label in [('clientes', 'Clientes'), ('processos', 'Processos'), ('agenda', 'Agendamentos')]:
        spec = RESOURCES[key]
        if request.user.has_perm(f'office.view_{spec.model._meta.model_name}'):
            count = spec.model.objects.count()
            if key == 'agenda':
                count = Agendamento.objects.filter(data_inicio__date=today).count()
                label = 'Agendamentos hoje'
            cards.append({'key': key, 'label': label, 'value': count})
    payments = None
    upcoming = None
    pending = None
    if request.user.has_perm('office.view_pagamento'):
        overdue = Pagamento.objects.filter(data_conclusao__isnull=True, data_limite__lt=today)
        total = overdue.aggregate(total=Sum('montante'))['total'] or Decimal('0')
        cards.append({'key': 'pagamentos', 'label': 'Valor em atraso', 'value': number_format(total, 2) + ' €'})
        payments = overdue.select_related('cliente')[:5]
    if request.user.has_perm('office.view_agendamento'):
        upcoming = Agendamento.objects.filter(data_inicio__gte=timezone.now()).select_related('cliente')[:5]
    if request.user.has_perm('office.view_documentocliente'):
        pending = DocumentoCliente.objects.filter(Q(entregue=False) | Q(entregue__isnull=True)).select_related('cliente')[:5]
    return render(request, 'office/dashboard.html', {'cards': cards, 'payments': payments, 'upcoming': upcoming, 'pending': pending, 'today': today})


@resource_access('view')
def record_list(request, resource, spec):
    records = queryset(spec)
    query = request.GET.get('q', '').strip()[:100]
    if query:
        search = Q()
        for field in spec.search:
            search |= Q(**{f'{field}__icontains': query})
        records = records.filter(search).distinct()
    selected_client = request.GET.get('cliente', '')
    if selected_client.isdigit() and 'cliente' in spec.fields:
        records = records.filter(cliente_id=int(selected_client))
    if resource == 'pagamentos' and request.GET.get('filtro') == 'atraso':
        records = records.filter(data_conclusao__isnull=True, data_limite__lt=timezone.localdate())
    page = Paginator(records, 25).get_page(request.GET.get('page'))
    rows = [{'object': obj, 'cells': [getattr(obj, field) for field in spec.columns]} for obj in page]
    headers = [spec.model._meta.get_field(field).verbose_name for field in spec.columns]
    return render(request, 'office/list.html', {
        'resource': resource, 'spec': spec, 'rows': rows, 'headers': headers,
        'page': page, 'query': query,
        'can_add': request.user.has_perm(f'office.add_{spec.model._meta.model_name}'),
    })


@resource_access('view')
def record_detail(request, resource, spec, pk):
    instance = get_object_or_404(queryset(spec), pk=pk)
    details = [(spec.model._meta.get_field(field).verbose_name, getattr(instance, field)) for field in spec.fields]
    related = []
    if resource == 'clientes':
        for key, manager in [('processos', 'processos'), ('pagamentos', 'pagamentos'), ('agenda', 'agendamentos'), ('documentos', 'documentos')]:
            model = RESOURCES[key].model
            if request.user.has_perm(f'office.view_{model._meta.model_name}'):
                related.append({'key': key, 'label': RESOURCES[key].title, 'objects': getattr(instance, manager).all()[:20]})
    elif resource == 'processos' and request.user.has_perm('office.view_etapa'):
        related.append({'key': 'etapas', 'label': 'Histórico de etapas', 'objects': instance.etapas.select_related('fase')[:50]})
    return render(request, 'office/detail.html', {
        'resource': resource, 'spec': spec, 'object': instance, 'details': details, 'related': related,
        'can_edit': request.user.has_perm(f'office.change_{spec.model._meta.model_name}'),
        'can_delete': request.user.has_perm(f'office.delete_{spec.model._meta.model_name}'),
        'can_sync': resource == 'agenda' and request.user.has_perm('office.sync_calendar'),
    })


@login_required
def record_edit(request, resource, pk=None):
    spec = RESOURCES.get(resource)
    if not spec:
        raise Http404
    action = 'change' if pk is not None else 'add'
    if not request.user.has_perm(f'office.{action}_{spec.model._meta.model_name}'):
        raise PermissionDenied
    instance = get_object_or_404(spec.model, pk=pk) if pk is not None else None
    initial = {}
    if request.GET.get('cliente', '').isdigit() and 'cliente' in spec.fields:
        initial['cliente'] = request.GET['cliente']
    form = record_form(spec)(request.POST if request.method == 'POST' else None, instance=instance, initial=initial)
    if request.method == 'POST' and form.is_valid():
        try:
            with transaction.atomic():
                obj = form.save()
                audit(request, action, obj)
        except IntegrityError:
            form.add_error(None, 'Este registo entra em conflito com dados existentes. Verifique os identificadores.')
        else:
            messages.success(request, 'Registo guardado com sucesso.')
            return redirect('record_detail', resource=resource, pk=obj.pk)
    return render(request, 'office/form.html', {'resource': resource, 'spec': spec, 'form': form, 'object': instance})


@resource_access('delete')
def record_delete(request, resource, spec, pk):
    instance = get_object_or_404(spec.model, pk=pk)
    if request.method == 'POST':
        try:
            with transaction.atomic():
                audit(request, 'delete', instance)
                instance.delete()
        except (ProtectedError, IntegrityError):
            messages.error(request, 'Existem registos associados. Remova as dependências antes de eliminar.')
            return redirect('record_detail', resource=resource, pk=pk)
        messages.success(request, 'Registo eliminado.')
        return redirect('record_list', resource=resource)
    return render(request, 'office/delete.html', {'resource': resource, 'object': instance})


@login_required
@permission_required('office.generate_document', raise_exception=True)
@permission_required('office.view_cliente', raise_exception=True)
def generate_document(request):
    from docxtpl import DocxTemplate
    from jinja2 import StrictUndefined
    from jinja2.sandbox import SandboxedEnvironment
    from num2words import num2words
    form = GenerationForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        client = form.cleaned_data['cliente']
        template = form.cleaned_data['modelo']
        context = {f.name: getattr(client, f.name) or '' for f in client._meta.fields if not f.is_relation}
        def fmt(value):
            return value.strftime('%d/%m/%Y') if value else ''
        context.update({
            'nome': client.nome_completo or '', 'nome_upper': (client.nome_completo or '').upper(),
            'endereço': ', '.join(str(v) for v in [client.rua, client.numero_rua, client.complemento, client.localidade, client.codigo_postal] if v),
            'data_documento': fmt(timezone.localdate()), 'titulo_residencia': client.titulo_residencia or '',
            'validade_titulo_residencia': fmt(client.validade_bi_cc),
            'validade_passaporte': fmt(client.validade_passaporte),
            'emissao_passaporte': fmt(client.emissao_passaporte),
            'local_emissao_passaporte': client.local_emissao_passaporte or '',
        })
        amount = form.cleaned_data.get('valor_contrato')
        installments = form.cleaned_data.get('numero_parcelas')
        if amount is not None:
            context['valor_contrato'] = f'{amount:.2f}'
            context['valor_contrato_string'] = num2words(amount, lang='pt', to='currency')
        if installments:
            context['numero_parcelas'] = installments
            if amount is not None:
                per_installment = (amount / installments).quantize(Decimal('0.01'))
                context['valor_contrato_div_parcelas'] = f'{per_installment:.2f}'
                context['valor_contrato_div_parcelas_string'] = num2words(per_installment, lang='pt', to='currency')
        start = form.cleaned_data.get('inicio_prestacao')
        if start:
            from django.utils.formats import date_format
            context['mes_ano_inicio_prestacao'] = date_format(start, 'F Y')
        missing = [field for field in template.required_fields if context.get(field, '') == '']
        if missing:
            form.add_error(None, 'Preencha os campos necessários: ' + ', '.join(missing))
        else:
            try:
                doc = DocxTemplate(template.file.path)
                doc.render(context, jinja_env=SandboxedEnvironment(undefined=StrictUndefined), autoescape=True)
                output = BytesIO()
                doc.save(output)
                output.seek(0)
            except Exception:
                form.add_error(None, 'Não foi possível gerar o documento. Peça ao administrador para verificar o modelo e os campos.')
            else:
                audit(request, 'generate', template)
                return FileResponse(output, as_attachment=True, filename=f'documento-{client.pk}-{template.pk}.docx')
    return render(request, 'office/generate.html', {'form': form})


@login_required
@permission_required('office.sync_calendar', raise_exception=True)
@permission_required('office.change_agendamento', raise_exception=True)
@require_POST
def calendar_sync(request, pk):
    from .google_calendar import sync_event
    obj = get_object_or_404(Agendamento, pk=pk)
    try:
        sync_event(obj)
    except Exception:
        messages.error(request, 'A sincronização falhou. Verifique a ligação Google, a data e a duração; o agendamento local foi preservado.')
    else:
        audit(request, 'google_sync', obj)
        messages.success(request, 'Agendamento sincronizado com o Google Calendar.')
    return redirect('record_detail', resource='agenda', pk=pk)


def health(request):
    from django.http import JsonResponse
    return JsonResponse({'status': 'ok'})


@login_required
@permission_required('office.view_pagamento', raise_exception=True)
def financial_report(request):
    from .financial_reports import build_report, preset_dates
    from .report_forms import FinancialReportForm
    today = timezone.localdate()
    start, end = preset_dates(request.GET.get('periodo', '6m'), today)
    data = request.GET.copy()
    # Explicit dates take precedence over presets; invalid submitted values
    # are displayed as errors and never silently replaced with a wider period.
    if 'inicio' not in data and 'fim' not in data:
        data['inicio'], data['fim'] = start.isoformat(), end.isoformat()
    form = FinancialReportForm(data)
    report = None
    if form.is_valid():
        start, end = form.cleaned_data['inicio'], form.cleaned_data['fim']
        client = form.cleaned_data.get('cliente')
        report = build_report(start, end, today, client.pk if client else None)
    return render(request, 'office/financial_report.html', {
        'resource': 'relatorios', 'form': form, 'report': report,
        'start': start, 'end': end, 'today': today,
    })
