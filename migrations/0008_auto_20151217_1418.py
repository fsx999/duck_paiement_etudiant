# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('duck_paiement_etudiant', '0007_auto_20151216_1507'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paiementparinscription',
            name='montant_paye',
            field=models.FloatField(null=True),
        ),
    ]
