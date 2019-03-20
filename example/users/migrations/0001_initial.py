from django.contrib.auth.models import User
from django.db import migrations


def create_users(apps, schema_editor):
    User.objects.create_user('Alice')
    User.objects.create_user('Bob')


class Migration(migrations.Migration):

    initial = True

    operations = [
        migrations.RunPython(create_users),
    ]
