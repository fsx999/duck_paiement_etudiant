# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('django_apogee', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AnneeUniPaiement',
            fields=[
                ('cod_anu', models.IntegerField(serialize=False, primary_key=True)),
                ('ouverture_paiement', models.CharField(default=False, max_length=1, choices=[(b'O', b'Ouverte'), (b'F', b'Ferm\xc3\xa9')])),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Banque',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nom', models.CharField(unique=True, max_length=100, verbose_name=b'Nom de la banque')),
            ],
            options={
                'ordering': ['nom'],
                'db_table': 'pal_banque',
                'verbose_name': 'banque',
                'verbose_name_plural': 'banques',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Bordereau',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('num_bordereau', models.IntegerField(verbose_name=b'Num\xc3\xa9ro bordereau')),
                ('num_paiement', models.IntegerField(null=True, verbose_name='Num\xe9ro de paiement', blank=True)),
                ('cloture', models.BooleanField(default=False, verbose_name='bordereau clotur\xe9')),
                ('date_cloture', models.DateField(null=True, verbose_name='Date de cloture du bordereau', blank=True)),
                ('envoi_mail', models.BooleanField(default=False, verbose_name='envoie mail')),
                ('type_paiement', models.CharField(max_length=1, verbose_name=b'type de paiement du bordereau', choices=[(b'C', 'Ch\xe8que ordinaire'), (b'B', 'Ch\xe8que de banque'), (b'E', 'Ch\xe8que \xe9tranger'), (b'V', 'Virement')])),
                ('type_bordereau', models.CharField(default=b'N', max_length=1, verbose_name=b'type de bordereau', choices=[(b'N', 'Normal'), (b'A', 'Auditeur Libre')])),
                ('comment', models.CharField(max_length=120, null=True, blank=True)),
                ('annee', models.ForeignKey(to='duck_paiement_etudiant.AnneeUniPaiement')),
            ],
            options={
                'ordering': ['type_bordereau', 'num_paiement', 'num_bordereau'],
                'get_latest_by': 'num_bordereau',
                'verbose_name': 'Bordereau',
                'verbose_name_plural': 'Bordereaux',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CalculTarif',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('total', models.FloatField(null=True, blank=True)),
                ('reste', models.FloatField(null=True, blank=True)),
                ('etape', models.ForeignKey(to='django_apogee.InsAdmEtp')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PaiementBackoffice',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('cod_etp', models.CharField(max_length=8, null=True, verbose_name='Code Etape', db_column=b'COD_ETP')),
                ('cod_vrs_vet', models.CharField(max_length=3, null=True, verbose_name='(COPIED)Numero Version Etape', db_column=b'COD_VRS_VET')),
                ('num_occ_iae', models.CharField(max_length=2, null=True, verbose_name='', db_column=b'NUM_OCC_IAE')),
                ('type', models.CharField(max_length=1, verbose_name=b'type paiement', choices=[(b'C', 'Ch\xe8que'), (b'B', 'Ch\xe8que de banque'), (b'E', 'Ch\xe8que \xe9tranger'), (b'V', 'Virement')])),
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
                ('cod_ind', models.ForeignKey(db_column=b'COD_IND', to='django_apogee.Individu', null=True)),
                ('etape', models.ForeignKey(related_name='paiements', to='django_apogee.InsAdmEtp', null=True)),
                ('nom_banque', models.ForeignKey(verbose_name='Nom de la banque', blank=True, to='duck_paiement_etudiant.Banque', null=True)),
            ],
            options={
                'ordering': ['id'],
                'db_table': 'pal_paiement_backoffice',
                'verbose_name': 'Paiement',
                'verbose_name_plural': 'Paiements',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SettingEtapePaiement',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('cod_anu', models.IntegerField(default=2014)),
                ('tarif', models.FloatField(null=True)),
                ('demi_annee', models.BooleanField(default=False, help_text=b"peut s'inscrire par semestre")),
                ('nb_paiment_max', models.IntegerField(default=2)),
                ('demi_tarif', models.BooleanField(default=False, help_text=b'demi tarif en cas de r\xc3\xa9ins')),
                ('etape', models.ForeignKey(related_name='settings_etape_paiement', to='django_apogee.Etape')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='InsAdmEtpPaiement',
            fields=[
            ],
            options={
                'verbose_name': "Inscription de l'\xe9tudiant",
                'proxy': True,
                'verbose_name_plural': 'Inscriptions des \xe9tudians',
            },
            bases=('django_apogee.insadmetp',),
        ),
    ]
