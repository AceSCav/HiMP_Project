from django.db import migrations, models
import django.core.validators


def normalize_timezone(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("SELECT data_type FROM information_schema.columns WHERE table_schema = current_schema() AND table_name = 'agendamento' AND column_name = 'data_inicio'")
        row = cursor.fetchone()
        if row and row[0] == 'timestamp without time zone':
            # The desktop stores Lisbon local wall time. Audit DST boundary records
            # on a staging copy before this explicit timezone interpretation.
            cursor.execute("ALTER TABLE agendamento ALTER COLUMN data_inicio TYPE timestamptz USING data_inicio AT TIME ZONE 'Europe/Lisbon'")


class Migration(migrations.Migration):
    dependencies = [('office', '0002_web_tables')]
    operations = [
        migrations.AlterField(model_name='pagamento', name='entidade', field=models.CharField('Entidade de pagamento', max_length=20, null=True, blank=True)),
        migrations.AlterField(model_name='pagamento', name='referencia', field=models.CharField('Referência', max_length=50, null=True, blank=True)),
        migrations.AlterField(model_name='pagamento', name='montante', field=models.DecimalField('Montante (€)', max_digits=14, decimal_places=2, null=True, blank=True, validators=[django.core.validators.MinValueValidator(0)])),
        # Deliberately irreversible: reverting financial types loses references and cents.
        migrations.RunPython(normalize_timezone),
    ]
