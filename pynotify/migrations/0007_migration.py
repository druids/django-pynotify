# Generated by Django 3.1 on 2021-08-23 11:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pynotify', '0006_add_send_push'),
    ]

    operations = [
        migrations.AddField(
            model_name='adminnotificationtemplate',
            name='is_locked',
            field=models.BooleanField(default=False),
        ),
    ]