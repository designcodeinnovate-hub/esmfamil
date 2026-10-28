# -*- coding: utf-8 -*-
from django.db import migrations


def forwards(apps, schema_editor):
    AllianceMember = apps.get_model("alliance", "AllianceMember")
    AllianceMember.objects.filter(role="officer").update(role="admin")


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [("alliance", "0001_initial")]
    operations = [migrations.RunPython(forwards, backwards)]
