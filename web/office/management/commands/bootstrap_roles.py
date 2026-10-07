from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from office.registry import RESOURCES


class Command(BaseCommand):
    help = 'Cria funções de consulta, gestão e administração sem criar contas nem senhas.'

    def handle(self, *args, **options):
        models = {r.model._meta.model_name for r in RESOURCES.values()}
        viewer = [f'view_{name}' for name in models]
        editor = viewer + [f'{action}_{name}' for name in models for action in ('add', 'change')]
        editor += ['generate_document', 'sync_calendar']
        manager = editor + [f'delete_{name}' for name in models]
        catalogues = ['configuration', 'entidade', 'tipoprocesso', 'fase', 'motivo', 'statuspagamento']
        manager += [f'{action}_{name}' for name in catalogues for action in ('view', 'add', 'change', 'delete')]
        manager += ['view_auditevent', 'view_documenttemplate']
        for name, codenames in [('Consulta', viewer), ('Gestão', editor), ('Administração', manager)]:
            group, _ = Group.objects.get_or_create(name=name)
            group.permissions.set(Permission.objects.filter(content_type__app_label='office', codename__in=codenames))
            self.stdout.write(self.style.SUCCESS(f'Função configurada: {name}'))
        self.stdout.write('Atribua as funções no admin. Apenas administradores de confiança devem ter is_staff; apenas o responsável técnico deve ser superuser.')
