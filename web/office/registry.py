from dataclasses import dataclass
from . import models

@dataclass(frozen=True)
class Resource:
    model: type
    title: str
    description: str
    fields: tuple
    columns: tuple
    search: tuple

RESOURCES = {
    'clientes': Resource(models.Cliente, 'Clientes', 'Pessoas, contactos e documentação num só lugar.',
        tuple(f.name for f in models.Cliente._meta.fields if not f.primary_key and f.editable),
        ('nome_completo', 'nif', 'email', 'contato', 'localidade'),
        ('nome_completo', 'nif', 'passaporte', 'titulo_residencia', 'email', 'processos__numero_processo')),
    'processos': Resource(models.Processo, 'Processos', 'Acompanhe cada processo e o seu histórico de etapas.',
        ('cliente', 'numero_processo', 'tipo', 'entidade', 'juiz', 'processo_anexo_principal'),
        ('numero_processo', 'cliente', 'tipo', 'entidade'), ('numero_processo', 'cliente__nome_completo')),
    'etapas': Resource(models.Etapa, 'Etapas', 'Registe a evolução dos processos.',
        ('processo', 'fase', 'data_fase', 'observacao'), ('processo', 'fase', 'data_fase', 'observacao'),
        ('processo__numero_processo', 'processo__cliente__nome_completo', 'fase__fase')),
    'pagamentos': Resource(models.Pagamento, 'Pagamentos', 'Prazos, referências e valores com precisão de cêntimos.',
        ('cliente', 'entidade', 'referencia', 'montante', 'data_limite', 'data_conclusao', 'status', 'motivo'),
        ('cliente', 'numero_parcela', 'montante', 'data_limite', 'status', 'referencia'), ('cliente__nome_completo', 'referencia')),
    'agenda': Resource(models.Agendamento, 'Agenda', 'Organize os atendimentos e sincronize com o Google Calendar.',
        ('cliente', 'titulo', 'data_inicio', 'duracao', 'motivo', 'descricao'),
        ('titulo', 'cliente', 'data_inicio', 'duracao', 'motivo'), ('titulo', 'cliente__nome_completo', 'motivo')),
    'documentos': Resource(models.DocumentoCliente, 'Documentos', 'Controle os documentos recebidos e por entregar.',
        ('cliente', 'documento_nome', 'entregue'), ('cliente', 'documento_nome', 'entregue'),
        ('cliente__nome_completo', 'documento_nome')),
}
