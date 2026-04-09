from django.db import migrations


def create_default_typeid(apps, schema_editor):
    TypeId = apps.get_model('identifier', 'TypeId')

    for name in ['qrcode', 'barcode']:
        TypeId.objects.get_or_create(name=name)


def reverse_func(apps, schema_editor):
    TypeId = apps.get_model('identifier', 'TypeId')
    TypeId.objects.filter(name__in=['qrcode', 'barcode']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('identifier', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_default_typeid, reverse_func),
    ]
