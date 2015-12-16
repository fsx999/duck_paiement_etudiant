# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('duck_inscription', '0007_auto_20150724_1223'),
        ('duck_paiement_etudiant', '0005_auto_20151215_1726'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='paiementparinscription',
            name='Individu',
        ),
        migrations.AddField(
            model_name='paiementparinscription',
            name='individu',
            field=models.ForeignKey(to='duck_inscription.Individu', null=True),
        ),
        migrations.AlterField(
            model_name='paiementparinscription',
            name='cod_anu',
            field=models.CharField(max_length=4, null=True),
        ),
        migrations.AlterField(
            model_name='paiementparinscription',
            name='cod_ind',
            field=models.CharField(max_length=10, null=True),
        ),
    ]
