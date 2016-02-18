# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('duck_paiement_etudiant', '0010_auto_20160201_1707'),
    ]

    operations = [
        migrations.AddField(
            model_name='paiementparinscription',
            name='droits',
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name='paiementparinscription',
            name='frais',
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name='paiementparinscription',
            name='montant_recu',
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name='paiementparinscription',
            name='montant_rembourse',
            field=models.FloatField(null=True),
        ),
    ]
