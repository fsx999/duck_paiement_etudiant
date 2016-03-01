# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('duck_paiement_etudiant', '0003_paiementparinscription'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paiementparinscription',
            name='cod_anu',
            field=models.CharField(max_length=4),
        ),
        migrations.AlterField(
            model_name='paiementparinscription',
            name='cod_etu',
            field=models.CharField(max_length=10),
        ),
        migrations.AlterField(
            model_name='paiementparinscription',
            name='cod_ind',
            field=models.CharField(max_length=10),
        ),
    ]
