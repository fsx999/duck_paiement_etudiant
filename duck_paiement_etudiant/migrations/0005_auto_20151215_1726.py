# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('django_apogee', '0003_auto_20151009_1115'),
        ('duck_paiement_etudiant', '0004_auto_20151215_1436'),
    ]

    operations = [
        migrations.AddField(
            model_name='paiementparinscription',
            name='Individu',
            field=models.ForeignKey(to='django_apogee.Individu', null=True),
        ),
        migrations.AlterField(
            model_name='paiementparinscription',
            name='cod_anu',
            field=models.CharField(default=b'2015', max_length=4),
        ),
    ]
