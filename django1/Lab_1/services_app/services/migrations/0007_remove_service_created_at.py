# Generated by Django 5.1.7 on 2025-04-22 09:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0006_service_created_at'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='service',
            name='created_at',
        ),
    ]
