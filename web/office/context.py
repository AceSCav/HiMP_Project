def navigation(request):
    items = [
        ('clientes', 'Clientes', 'office.view_cliente'),
        ('processos', 'Processos', 'office.view_processo'),
        ('etapas', 'Etapas', 'office.view_etapa'),
        ('pagamentos', 'Pagamentos', 'office.view_pagamento'),
        ('agenda', 'Agenda', 'office.view_agendamento'),
        ('documentos', 'Documentos', 'office.view_documentocliente'),
    ]
    return {'navigation': [(key, label) for key, label, perm in items if request.user.has_perm(perm)]}
