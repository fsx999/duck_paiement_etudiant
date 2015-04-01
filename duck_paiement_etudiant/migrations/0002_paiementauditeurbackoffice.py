# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('foad', '0001_initial'),
        ('duck_paiement_etudiant', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PaiementAuditeurBackoffice',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('cod_etp', models.CharField(max_length=8, null=True, verbose_name='Code Etape', db_column=b'COD_ETP')),
                ('type', models.CharField(max_length=1, verbose_name=b'type paiement', choices=[(b'C', 'Ch\xe9que'), (b'B', 'Ch\xe8que de banque'), (b'E', 'Ch\xe8que \xe9tranger'), (b'V', 'Virement')])),
                ('num_cheque', models.CharField(max_length=30, null=True, verbose_name=b'Num\xc3\xa9ro de ch\xc3\xa9que', blank=True)),
                ('autre_payeur', models.CharField(max_length=30, null=True, verbose_name=b'Autre payeur', blank=True)),
                ('somme', models.FloatField(verbose_name=b'Somme')),
                ('date', models.DateField(null=True, verbose_name=b'date pr\xc3\xa9vue', blank=True)),
                ('date_virement', models.DateField(null=True, verbose_name=b'Date du virement effectu\xc3\xa9', blank=True)),
                ('date_saisi', models.DateField(auto_now=True)),
                ('is_not_ok', models.BooleanField(default=False, verbose_name='Impay\xe9')),
                ('num_paiement', models.IntegerField(null=True, verbose_name='Num\xe9ro de paiement', blank=True)),
                ('observation', models.CharField(max_length=100, null=True, verbose_name='Observation', blank=True)),
                ('bordereau', models.ForeignKey(verbose_name=b'Bordereau', blank=True, to='duck_paiement_etudiant.Bordereau', null=True)),
                ('cod_anu', models.ForeignKey(db_column=b'COD_ANU', verbose_name='Code Annee Universitaire', to='duck_paiement_etudiant.AnneeUniPaiement', null=True)),
                ('etape', models.ForeignKey(related_name='paiements', to='foad.AuditeurLibreApogee')),
                ('nom_banque', models.ForeignKey(verbose_name='Nom de la banque', blank=True, to='duck_paiement_etudiant.Banque', null=True)),
            ],
            options={
                'verbose_name': 'Paiement',
                'verbose_name_plural': 'Paiements',
            },
            bases=(models.Model,),
        ),
    ]
