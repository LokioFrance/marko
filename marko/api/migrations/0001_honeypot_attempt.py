import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='HoneypotAttempt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip', models.CharField(max_length=45)),
                ('user_agent', models.TextField(default='')),
                ('path', models.CharField(max_length=255)),
                ('method', models.CharField(max_length=10)),
                ('username', models.CharField(blank=True, default='', max_length=255)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'ordering': ['-timestamp'],
            },
        ),
    ]
