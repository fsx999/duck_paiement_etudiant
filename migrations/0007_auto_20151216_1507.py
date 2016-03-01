# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('duck_paiement_etudiant', '0006_auto_20151215_2236'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paiementparinscription',
            name='wish',
            field=models.ForeignKey(null=True, to='duck_inscription.Wish', unique=True),
        ),
    ]
