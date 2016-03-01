# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('duck_paiement_etudiant', '0009_auto_20151217_1556'),
    ]

    operations = [
        migrations.AddField(
            model_name='paiementparinscription',
            name='date_encaissement',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='paiementparinscription',
            name='is_partiel',
            field=models.BooleanField(default=False, verbose_name='Is the paiement partial? (there was an error in one of the payments)'),
        ),
    ]
