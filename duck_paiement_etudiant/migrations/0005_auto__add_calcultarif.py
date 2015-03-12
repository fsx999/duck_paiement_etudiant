# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'CalculTarif'
        db.create_table(u'duck_paiement_etudiant_calcultarif', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('etape', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['django_apogee.InsAdmEtp'])),
            ('total', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('reste', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'duck_paiement_etudiant', ['CalculTarif'])


    def backwards(self, orm):
        # Deleting model 'CalculTarif'
        db.delete_table(u'duck_paiement_etudiant_calcultarif')


    models = {
        u'django_apogee.anneeuni': {
            'Meta': {'ordering': "[u'-cod_anu']", 'object_name': 'AnneeUni', 'db_table': "u'ANNEE_UNI'"},
            'cod_anu': ('django.db.models.fields.CharField', [], {'max_length': '4', 'primary_key': 'True', 'db_column': "u'COD_ANU'"}),
            'eta_anu_iae': ('django.db.models.fields.CharField', [], {'default': "u'I'", 'max_length': '1', 'db_column': "u'ETA_ANU_IAE'"})
        },
        u'django_apogee.etape': {
            'Meta': {'object_name': 'Etape', 'db_table': "u'ETAPE'"},
            'cod_cur': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'db_column': "u'COD_CUR'"}),
            'cod_cyc': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'db_column': "u'COD_CYC'"}),
            'cod_etp': ('django.db.models.fields.CharField', [], {'max_length': '6', 'primary_key': 'True', 'db_column': "u'COD_ETP'"}),
            'lib_etp': ('django.db.models.fields.CharField', [], {'max_length': '60', 'null': 'True', 'db_column': "u'LIB_ETP'"})
        },
        u'django_apogee.individu': {
            'Meta': {'object_name': 'Individu', 'db_table': "u'INDIVIDU'"},
            'cod_cle_nne_ind': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'db_column': "u'COD_CLE_NNE_IND'"}),
            'cod_etb': ('django.db.models.fields.CharField', [], {'max_length': '8', 'null': 'True', 'db_column': "u'COD_ETB'"}),
            'cod_etu': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'db_column': "u'COD_ETU'"}),
            'cod_fam': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'db_column': "u'COD_FAM'"}),
            'cod_ind': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True', 'db_column': "u'COD_IND'"}),
            'cod_ind_opi': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'db_column': "u'COD_IND_OPI'"}),
            'cod_nne_ind': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'db_column': "u'COD_NNE_IND'"}),
            'cod_pay_nat': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'db_column': "u'COD_PAY_NAT'"}),
            'cod_sex_etu': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'db_column': "u'COD_SEX_ETU'"}),
            'cod_sim': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'db_column': "u'COD_SIM'"}),
            'cod_thp': ('django.db.models.fields.CharField', [], {'max_length': '2', 'null': 'True', 'db_column': "u'COD_THP'"}),
            'cod_uti': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'db_column': "u'COD_UTI'"}),
            'daa_ens_sup': ('django.db.models.fields.CharField', [], {'max_length': '4', 'null': 'True', 'db_column': "u'DAA_ENS_SUP'"}),
            'daa_ent_etb': ('django.db.models.fields.CharField', [], {'max_length': '4', 'null': 'True', 'db_column': "u'DAA_ENT_ETB'"}),
            'daa_etb': ('django.db.models.fields.CharField', [], {'max_length': '4', 'null': 'True', 'db_column': "u'DAA_ETB'"}),
            'daa_lbt_ind': ('django.db.models.fields.CharField', [], {'max_length': '4', 'null': 'True', 'db_column': "u'DAA_LBT_IND'"}),
            'dat_cre_ind': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_column': "u'DAT_CRE_IND'"}),
            'dat_mod_ind': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_column': "u'DAT_MOD_IND'"}),
            'date_nai_ind': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_column': "u'DATE_NAI_IND'"}),
            'dmm_lbt_ind': ('django.db.models.fields.CharField', [], {'max_length': '2', 'null': 'True', 'db_column': "u'DMM_LBT_IND'"}),
            'lib_nom_pat_ind': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'db_column': "u'LIB_NOM_PAT_IND'"}),
            'lib_nom_usu_ind': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'db_column': "u'LIB_NOM_USU_IND'"}),
            'lib_pr1_ind': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'db_column': "u'LIB_PR1_IND'"}),
            'lib_pr2_ind': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'db_column': "u'LIB_PR2_IND'"}),
            'lib_pr3_ind': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'db_column': "u'LIB_PR3_IND'"}),
            'tem_date_nai_rel': ('django.db.models.fields.CharField', [], {'default': "u'O'", 'max_length': '1', 'null': 'True', 'db_column': "u'TEM_DATE_NAI_REL'"})
        },
        u'django_apogee.insadmetp': {
            'Meta': {'object_name': 'InsAdmEtp', 'db_table': "u'INS_ADM_ETP_COPY'"},
            'cod_anu': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['django_apogee.AnneeUni']"}),
            'cod_cge': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'db_column': "u'COD_CGE'"}),
            'cod_dip': ('django.db.models.fields.CharField', [], {'max_length': '7', 'null': 'True', 'db_column': "u'COD_DIP'"}),
            'cod_etp': ('django.db.models.fields.CharField', [], {'max_length': '8', 'null': 'True', 'db_column': "u'COD_ETP'"}),
            'cod_ind': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'etapes_ied'", 'db_column': "u'COD_IND'", 'to': u"orm['django_apogee.Individu']"}),
            'cod_pru': ('django.db.models.fields.CharField', [], {'max_length': '2', 'null': 'True', 'db_column': "u'COD_PRU'"}),
            'cod_vrs_vdi': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'db_column': "u'COD_VRS_VDI'"}),
            'cod_vrs_vet': ('django.db.models.fields.CharField', [], {'max_length': '3', 'db_column': "u'COD_VRS_VET'"}),
            'dat_annul_res_iae': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_column': "u'DAT_ANNUL_RES_IAE'"}),
            'dat_cre_iae': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_column': "u'DAT_CRE_IAE'"}),
            'dat_mod_iae': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_column': "u'DAT_MOD_IAE'"}),
            'demi_annee': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'eta_iae': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'db_column': "u'ETA_IAE'"}),
            'eta_pmt_iae': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'db_column': "u'ETA_PMT_IAE'"}),
            'exoneration': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'force_encaissement': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '30', 'primary_key': 'True'}),
            'nbr_ins_cyc': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'db_column': "u'NBR_INS_CYC'"}),
            'nbr_ins_dip': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'db_column': "u'NBR_INS_DIP'"}),
            'nbr_ins_etp': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'db_column': "u'NBR_INS_ETP'"}),
            'num_occ_iae': ('django.db.models.fields.CharField', [], {'max_length': '2', 'null': 'True', 'db_column': "u'NUM_OCC_IAE'"}),
            'tem_iae_prm': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'db_column': "u'TEM_IAE_PRM'"})
        },
        u'duck_paiement_etudiant.anneeunipaiement': {
            'Meta': {'object_name': 'AnneeUniPaiement'},
            'cod_anu': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'ouverture_paiement': ('django.db.models.fields.CharField', [], {'default': 'False', 'max_length': '1'})
        },
        u'duck_paiement_etudiant.banque': {
            'Meta': {'ordering': "['nom']", 'object_name': 'Banque', 'db_table': "u'pal_banque'"},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nom': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'})
        },
        u'duck_paiement_etudiant.bordereau': {
            'Meta': {'ordering': "['type_bordereau', 'num_paiement', 'num_bordereau']", 'object_name': 'Bordereau'},
            'annee': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['duck_paiement_etudiant.AnneeUniPaiement']"}),
            'cloture': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'date_cloture': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'envoi_mail': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'num_bordereau': ('django.db.models.fields.IntegerField', [], {}),
            'num_paiement': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'type_bordereau': ('django.db.models.fields.CharField', [], {'default': "'N'", 'max_length': '1'}),
            'type_paiement': ('django.db.models.fields.CharField', [], {'max_length': '1'})
        },
        u'duck_paiement_etudiant.calcultarif': {
            'Meta': {'object_name': 'CalculTarif'},
            'etape': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['django_apogee.InsAdmEtp']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'reste': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'total': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'})
        },
        u'duck_paiement_etudiant.paiementbackoffice': {
            'Meta': {'ordering': "['id']", 'object_name': 'PaiementBackoffice', 'db_table': "u'pal_paiement_backoffice'"},
            'autre_payeur': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'bordereau': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['duck_paiement_etudiant.Bordereau']", 'null': 'True', 'blank': 'True'}),
            'cod_anu': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['duck_paiement_etudiant.AnneeUniPaiement']", 'null': 'True', 'db_column': "'COD_ANU'"}),
            'cod_etp': ('django.db.models.fields.CharField', [], {'max_length': '8', 'null': 'True', 'db_column': "'COD_ETP'"}),
            'cod_ind': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['django_apogee.Individu']", 'null': 'True', 'db_column': "'COD_IND'"}),
            'cod_vrs_vet': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'db_column': "'COD_VRS_VET'"}),
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'date_saisi': ('django.db.models.fields.DateField', [], {'auto_now': 'True', 'blank': 'True'}),
            'date_virement': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'etape': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'paiements'", 'null': 'True', 'to': u"orm['django_apogee.InsAdmEtp']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_not_ok': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'nom_banque': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['duck_paiement_etudiant.Banque']", 'null': 'True', 'blank': 'True'}),
            'num_cheque': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'num_occ_iae': ('django.db.models.fields.CharField', [], {'max_length': '2', 'null': 'True', 'db_column': "'NUM_OCC_IAE'"}),
            'num_paiement': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'observation': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'somme': ('django.db.models.fields.FloatField', [], {}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '1'})
        },
        u'duck_paiement_etudiant.settingetapepaiement': {
            'Meta': {'object_name': 'SettingEtapePaiement'},
            'cod_anu': ('django.db.models.fields.IntegerField', [], {'default': '2014'}),
            'demi_annee': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'demi_tarif': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'etape': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'settings_etape_paiement'", 'to': u"orm['django_apogee.Etape']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nb_paiment_max': ('django.db.models.fields.IntegerField', [], {'default': '2'}),
            'tarif': ('django.db.models.fields.FloatField', [], {'null': 'True'})
        }
    }

    complete_apps = ['duck_paiement_etudiant']