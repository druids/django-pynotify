# Generated by Django 3.2.11 on 2022-02-28 00:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pynotify', '0008_migration'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='notificationtemplate',
            unique_together={('title', 'text', 'trigger_action', 'extra_fields', 'admin_template')},
        ),
    ]
