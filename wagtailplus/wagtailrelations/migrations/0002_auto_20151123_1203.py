# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailrelations', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='category',
            options={'ordering': ('path',), 'verbose_name': 'Category', 'verbose_name_plural': 'Categories'},
        ),
        migrations.RemoveField(
            model_name='entry',
            name='url',
        ),
    ]
