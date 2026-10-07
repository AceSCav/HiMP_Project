from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Configuration(models.Model):
    class Category(models.TextChoices):
        MARITAL = 'estado_civil', 'Estados civis'
        GENDER = 'genero', 'Géneros'
        REASON = 'motivo_agenda', 'Motivos de agendamento'
        DURATION = 'duracao_agenda', 'Durações de agendamento'
        DOCUMENT = 'documento', 'Documentos solicitados'
    category = models.CharField('Categoria', max_length=30, choices=Category.choices)
    label = models.CharField('Nome', max_length=300)
    minutes = models.PositiveIntegerField('Minutos (para durações)', null=True, blank=True, validators=[MinValueValidator(1)])
    active = models.BooleanField('Ativo', default=True)
    order = models.PositiveIntegerField('Ordem', default=0)

    class Meta:
        ordering = ['order', 'label']
        constraints = [models.UniqueConstraint(fields=['category', 'label'], name='unique_configuration_label')]
        verbose_name = 'Opção configurável'
        verbose_name_plural = 'Opções configuráveis'

    def __str__(self):
        return self.label


class Cliente(models.Model):
    drive_folder_id = models.CharField(max_length=200, blank=True, editable=False)
    cliente_id = models.AutoField(primary_key=True)
    nome_completo = models.TextField('Nome completo', null=True, blank=True)
    nif = models.TextField('NIF', null=True, blank=True, unique=True)
    niss = models.TextField('NISS', null=True, blank=True, unique=True)
    passaporte = models.TextField('Passaporte', null=True, blank=True, unique=True)
    titulo_residencia = models.TextField('BI / CC / título de residência', db_column='bi_cc_titulo_residência', null=True, blank=True, unique=True)
    data_nascimento = models.DateField('Data de nascimento', null=True, blank=True)
    genero = models.TextField('Género', db_column='gênero', null=True, blank=True)
    estado_civil = models.TextField('Estado civil', null=True, blank=True)
    email = models.EmailField('Email', null=True, blank=True)
    ddi = models.BigIntegerField('Indicativo telefónico', null=True, blank=True)
    contato = models.TextField('Telefone', null=True, blank=True)
    rua = models.TextField('Rua', null=True, blank=True)
    numero_rua = models.TextField('Número', null=True, blank=True)
    complemento = models.TextField('Complemento', null=True, blank=True)
    localidade = models.TextField('Localidade', null=True, blank=True)
    codigo_postal = models.TextField('Código postal', db_column='código_postal', null=True, blank=True)
    profissao = models.TextField('Profissão', db_column='profissão', null=True, blank=True)
    nacionalidade = models.TextField('Nacionalidade', null=True, blank=True)
    naturalidade = models.TextField('Naturalidade', null=True, blank=True)
    validade_passaporte = models.DateField('Validade do passaporte', null=True, blank=True)
    emissao_passaporte = models.DateField('Emissão do passaporte', db_column='emissão_passaporte', null=True, blank=True)
    local_emissao_passaporte = models.TextField('Local de emissão', db_column='local_emissão_passaporte', null=True, blank=True)
    validade_bi_cc = models.DateField('Validade do BI / CC', null=True, blank=True)
    emissao_bi_cc = models.DateField('Emissão do BI / CC', db_column='emissão_bi_cc', null=True, blank=True)
    notas_documento = models.TextField('Notas', null=True, blank=True)

    class Meta:
        db_table = 'cliente'
        ordering = ['nome_completo', 'cliente_id']
        verbose_name = 'Cliente'

    def __str__(self):
        return self.nome_completo or f'Cliente {self.pk}'


class Entidade(models.Model):
    entidade_id = models.BigAutoField(primary_key=True)
    entidade = models.TextField('Nome')
    class Meta:
        db_table = 'entidade'
        ordering = ['entidade']
        verbose_name = 'Entidade'
    def __str__(self):
        return self.entidade


class TipoProcesso(models.Model):
    tipo_do_processo_id = models.BigAutoField(primary_key=True)
    tipo_do_processo = models.TextField('Nome')
    class Meta:
        db_table = 'tipo_do_processo'
        ordering = ['tipo_do_processo']
        verbose_name = 'Tipo de processo'
        verbose_name_plural = 'Tipos de processo'
    def __str__(self):
        return self.tipo_do_processo


class Fase(models.Model):
    fase_id = models.BigAutoField(primary_key=True)
    fase = models.TextField('Nome')
    class Meta:
        db_table = 'lista_fases_processo'
        ordering = ['fase']
        verbose_name = 'Fase de processo'
        verbose_name_plural = 'Fases de processo'
    def __str__(self):
        return self.fase


class Processo(models.Model):
    processo_id = models.BigAutoField(primary_key=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, db_column='cliente_id', related_name='processos')
    entidade = models.ForeignKey(Entidade, on_delete=models.PROTECT, db_column='entidade_id', null=True, blank=True)
    tipo = models.ForeignKey(TipoProcesso, on_delete=models.PROTECT, db_column='tipo_do_processo_id', null=True, blank=True)
    juiz = models.TextField('Juiz', null=True, blank=True)
    numero_processo = models.TextField('Número do processo', null=True, blank=True, unique=True)
    processo_anexo_principal = models.TextField('Referência do anexo principal', null=True, blank=True)
    class Meta:
        db_table = 'processo'
        ordering = ['-processo_id']
        verbose_name = 'Processo'
    def __str__(self):
        return self.numero_processo or f'Processo {self.pk}'


class Etapa(models.Model):
    etapa_id = models.BigAutoField(primary_key=True)
    processo = models.ForeignKey(Processo, on_delete=models.PROTECT, db_column='processo_id', related_name='etapas')
    fase = models.ForeignKey(Fase, on_delete=models.PROTECT, db_column='fase_id', null=True, blank=True)
    data_fase = models.DateField('Data da fase', null=True, blank=True)
    observacao = models.TextField('Observação', db_column='observação', null=True, blank=True)
    class Meta:
        db_table = 'etapa_processo'
        ordering = ['-data_fase', '-etapa_id']
        verbose_name = 'Etapa'
    def __str__(self):
        return f'{self.processo} · {self.fase or "Sem fase"}'


class Motivo(models.Model):
    motivo_id = models.BigAutoField(primary_key=True)
    motivo = models.TextField('Nome')
    class Meta:
        db_table = 'motivo'
        ordering = ['motivo']
        verbose_name = 'Motivo de pagamento'
        verbose_name_plural = 'Motivos de pagamento'
    def __str__(self):
        return self.motivo


class StatusPagamento(models.Model):
    status_id = models.BigAutoField(primary_key=True)
    status = models.TextField('Nome')
    class Meta:
        db_table = 'status_pagamento'
        ordering = ['status']
        verbose_name = 'Estado de pagamento'
        verbose_name_plural = 'Estados de pagamento'
    def __str__(self):
        return self.status


class Pagamento(models.Model):
    plano_id = models.UUIDField(null=True, blank=True, editable=False, db_index=True)
    numero_parcela = models.PositiveSmallIntegerField('Parcela', null=True, blank=True, editable=False)
    total_parcelas = models.PositiveSmallIntegerField(null=True, blank=True, editable=False)
    pagamento_id = models.BigAutoField(primary_key=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, db_column='cliente_id', null=True, blank=True, related_name='pagamentos')
    entidade = models.CharField('Entidade de pagamento', max_length=20, null=True, blank=True)
    referencia = models.CharField('Referência', max_length=50, null=True, blank=True)
    montante = models.DecimalField('Montante (€)', max_digits=14, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    data_limite = models.DateField('Data limite', null=True, blank=True)
    data_conclusao = models.DateField('Data de conclusão', null=True, blank=True)
    status = models.ForeignKey(StatusPagamento, on_delete=models.PROTECT, db_column='status_id', null=True, blank=True)
    motivo = models.ForeignKey(Motivo, on_delete=models.PROTECT, db_column='motivo_id', null=True, blank=True)
    class Meta:
        db_table = 'pagamento'
        ordering = ['data_limite', '-pagamento_id']
        verbose_name = 'Pagamento'
    def __str__(self):
        label = f'Parcela {self.numero_parcela} de {self.total_parcelas}' if self.plano_id else f'Pagamento {self.pk}'
        return f'{label} · {self.cliente or "Sem cliente"}'


class Agendamento(models.Model):
    evento_id = models.BigAutoField(primary_key=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, db_column='cliente_id', null=True, blank=True, related_name='agendamentos')
    titulo = models.TextField('Título', null=True, blank=True)
    data_inicio = models.DateTimeField('Data e hora de início', null=True, blank=True)
    duracao = models.TextField('Duração', null=True, blank=True)
    motivo = models.TextField('Motivo', null=True, blank=True)
    descricao = models.TextField('Descrição', null=True, blank=True)
    google_event_id = models.TextField(null=True, blank=True)
    class Meta:
        db_table = 'agendamento'
        ordering = ['data_inicio', 'evento_id']
        verbose_name = 'Agendamento'
        permissions = [('sync_calendar', 'Pode sincronizar a agenda Google')]
    def __str__(self):
        return self.titulo or f'Agendamento {self.pk}'


class DocumentoCliente(models.Model):
    drive_file_id = models.CharField(max_length=200, blank=True, editable=False)
    drive_filename = models.CharField(max_length=255, blank=True, editable=False)
    id = models.AutoField(primary_key=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, db_column='cliente_id', related_name='documentos')
    documento_nome = models.TextField('Documento')
    entregue = models.BooleanField('Entregue', null=True, blank=True, default=False)
    class Meta:
        db_table = 'documentos_cliente'
        ordering = ['documento_nome']
        verbose_name = 'Documento do cliente'
        verbose_name_plural = 'Documentos do cliente'
    def __str__(self):
        return self.documento_nome


class DocumentTemplate(models.Model):
    name = models.CharField('Nome', max_length=200, unique=True)
    file = models.FileField('Modelo DOCX', upload_to='templates/%Y/%m/')
    required_fields = models.JSONField('Campos obrigatórios', default=list)
    active = models.BooleanField('Ativo', default=True)
    class Meta:
        ordering = ['name']
        verbose_name = 'Modelo de documento'
        verbose_name_plural = 'Modelos de documento'
        permissions = [('generate_document', 'Pode gerar documentos')]
    def __str__(self):
        return self.name


class CalendarConnection(models.Model):
    # A shared office calendar; tokens must never be displayed in admin/forms.
    key = models.CharField(max_length=30, unique=True, default='office')
    encrypted_credentials = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)


class DriveConnection(models.Model):
    key = models.CharField(max_length=30, unique=True, default='office')
    encrypted_credentials = models.TextField()
    root_folder_id = models.CharField(max_length=200, blank=True)
    updated_at = models.DateTimeField(auto_now=True)


class AuditEvent(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=30)
    model = models.CharField(max_length=80)
    object_id = models.CharField(max_length=80)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Registo de auditoria'
        verbose_name_plural = 'Registos de auditoria'
