# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('duck_paiement_etudiant', '0008_auto_20151217_1418'),
    ]

    operations = [
        migrations.AddField(
            model_name='paiementparinscription',
            name='annee',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='paiementparinscription',
            name='nom',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='paiementparinscription',
            name='num_commande',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='paiementparinscription',
            name='prenom',
            field=models.CharField(max_length=255, null=True),
        ),
    ]
