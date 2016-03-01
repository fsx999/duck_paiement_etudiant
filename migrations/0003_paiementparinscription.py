# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('duck_inscription', '0006_auto_20150723_1117'),
        ('django_apogee', '0003_auto_20151009_1115'),
        ('duck_paiement_etudiant', '0002_paiementauditeurbackoffice'),
    ]

    operations = [
        migrations.CreateModel(
            name='PaiementParInscription',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('cod_etp', models.CharField(max_length=8, null=True, verbose_name='Code Etape', db_column=b'COD_ETP')),
                ('cod_vrs_vet', models.CharField(max_length=3, null=True, verbose_name='(COPIED)Numero Version Etape', db_column=b'COD_VRS_VET')),
                ('num_occ_iae', models.CharField(max_length=2, null=True, verbose_name='', db_column=b'NUM_OCC_IAE')),
                ('cod_etu', models.IntegerField(null=True, verbose_name='Code Etudiant', db_column=b'COD_ETU')),
                ('montant_paye', models.IntegerField(null=True)),
                ('paiment_type', models.CharField(max_length=3, null=True, verbose_name='Paiement Type')),
                ('bordereau', models.IntegerField(null=True)),
                ('cod_anu', models.ForeignKey(db_column=b'COD_ANU', verbose_name='Code Annee Universitaire', to='duck_paiement_etudiant.AnneeUniPaiement', null=True)),
                ('cod_ind', models.ForeignKey(db_column=b'COD_IND', to='django_apogee.Individu', null=True)),
                ('wish', models.ForeignKey(to='duck_inscription.Wish', null=True)),
            ],
        ),
    ]
