from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from office import models

LEGACY = [models.Cliente, models.Entidade, models.TipoProcesso, models.Fase, models.Processo, models.Etapa, models.Motivo, models.StatusPagamento, models.Pagamento, models.Agendamento, models.DocumentoCliente]


class Command(BaseCommand):
    help = 'Verifica tabelas/colunas do desktop antes de migrate --fake-initial; não altera dados.'

    def handle(self, *args, **options):
        failures = []
        with connection.cursor() as cursor:
            tables = set(connection.introspection.table_names(cursor))
            for model in LEGACY:
                table = model._meta.db_table
                if table not in tables:
                    failures.append(f'Falta a tabela {table}')
                    continue
                actual = {col.name for col in connection.introspection.get_table_description(cursor, table)}
                required = {field.column for field in model._meta.fields}
                missing = required - actual
                if missing:
                    failures.append(f'{table}: faltam colunas {sorted(missing)}')
                else:
                    self.stdout.write(f'{table}: colunas presentes')
            if 'pagamento' in tables and connection.vendor == 'postgresql':
                cursor.execute("SELECT count(*) FROM pagamento WHERE montante < 0 OR montante::text IN ('NaN', 'Infinity', '-Infinity') OR abs(montante) >= 1000000000000")
                if cursor.fetchone()[0]:
                    failures.append('Há montantes inválidos ou fora do limite. Corrija-os na cópia de staging antes da migração.')
        if failures:
            raise CommandError('\n'.join(failures))
        self.stdout.write(self.style.SUCCESS('Pré-verificação concluída. Ainda é necessário comparar tipos, constraints, timezone e dados numa cópia de staging.'))
