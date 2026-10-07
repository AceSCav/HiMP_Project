import json
from pathlib import Path
from django.db import migrations


def seed_catalogues(apps, schema_editor):
    Configuration = apps.get_model('office', 'Configuration')
    DocumentTemplate = apps.get_model('office', 'DocumentTemplate')
    alias = schema_editor.connection.alias
    defaults = json.loads((Path(__file__).parent.parent / 'legacy_defaults.json').read_text(encoding='utf-8'))
    for category, labels in defaults.items():
        if category == 'templates':
            continue
        for index, label in enumerate(labels):
            minutes = None
            if category == 'duracao_agenda':
                minutes = int(label.split()[0]) * (60 if 'Hora' in label else 1)
            Configuration.objects.using(alias).get_or_create(category=category, label=label, defaults={'order': index, 'minutes': minutes})
    # Include values already stored by desktop users, preserving their exact spelling.
    for model, field, category in [('Cliente', 'estado_civil', 'estado_civil'), ('Cliente', 'genero', 'genero'), ('Agendamento', 'motivo', 'motivo_agenda'), ('Agendamento', 'duracao', 'duracao_agenda'), ('DocumentoCliente', 'documento_nome', 'documento')]:
        for label in apps.get_model('office', model).objects.using(alias).exclude(**{f'{field}__isnull': True}).exclude(**{field: ''}).values_list(field, flat=True).distinct():
            Configuration.objects.using(alias).get_or_create(category=category, label=label)
    for name, metadata in defaults['templates'].items():
        # This repository contains no DOCX files. Keep imported models inactive
        # until a trusted administrator uploads the real template.
        DocumentTemplate.objects.using(alias).get_or_create(name=name, defaults={'file': '', 'active': False, 'required_fields': metadata['campos']})


class Migration(migrations.Migration):
    dependencies = [('office', '0003_financial_and_timezone')]
    operations = [migrations.RunPython(seed_catalogues, migrations.RunPython.noop)]
