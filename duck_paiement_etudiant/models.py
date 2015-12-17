# -*- coding: utf-8 -*-
import tempfile
from django.conf import settings

from django.db import models
import unicodedata
from django.db.models import Sum
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template import Template, Context
from django.template.loader import render_to_string
from django.utils.encoding import python_2_unicode_compatible
from duck_inscription.models import Wish, Individu as Individu2
from mailrobot.models import MailBody, Mail
from duck_utils.utils import email_ied, get_recipients
from foad.models import AuditeurLibreApogee
from .managers import BordereauManager, BordereauAuditeurManager, PaiementBackofficeManager
from django_apogee.models import InsAdmEtp, AnneeUni, Individu, Etape
from datetime import date
import time
from wkhtmltopdf.utils import wkhtmltopdf
from duck_utils.models import TemplateHtmlModel


class InsAdmEtpPaiement(InsAdmEtp):
    class Meta:
        proxy = True
        verbose_name = 'Inscription de l\'étudiant'
        verbose_name_plural = 'Inscriptions des étudians'

    @property
    def settings_etape_paiement(self):
        if not hasattr(self, '_settings_etape_paiement'):
            self._settings_etape_paiement = SettingEtapePaiement.objects.get(etape__cod_etp=self.cod_etp,
                                                                             cod_anu=self.cod_anu.cod_anu)
        return self._settings_etape_paiement

    def get_total(self):
        tarif = self.settings_etape_paiement.get_tarif_paiement(reins=self.is_reins, semestre=self.demi_annee)
        if self.exoneration:
            if self.exoneration == 'T':
                tarif = 0
            elif self.exoneration == 'P':
                tarif /= 2.0
        return tarif

    def get_tarif(self):
        tarif = self.settings_etape_paiement.get_tarif_paiement(reins=self.is_reins, semestre=self.demi_annee)
        if self.exoneration:
            if self.exoneration == 'T':
                tarif = 0
            elif self.exoneration == 'P':
                tarif /= 2.0
        total_payer = 0
        for x in self.paiements.filter(is_not_ok=False):
            total_payer += x.somme
        reste = tarif - total_payer
        return "Total : %s | Saisi : %s | Reste %s" % (tarif, total_payer, reste)
    get_tarif.short_description = "Tarif"

    def get_reste(self):
        tarif = self.settings_etape_paiement.get_tarif_paiement(reins=self.is_reins, semestre=self.demi_annee)
        if self.exoneration:
            if self.exoneration == 'T':
                tarif = 0
            elif self.exoneration == 'P':
                tarif /= 2.0
        total_payer = 0
        for x in self.paiements.filter(is_not_ok=False):
            total_payer += x.somme
        reste = tarif - total_payer
        return reste


class CalculTarif(models.Model):
    etape = models.ForeignKey(InsAdmEtp)
    total = models.FloatField(null=True, blank=True)
    reste = models.FloatField(null=True, blank=True)


@python_2_unicode_compatible
class AnneeUniPaiement(models.Model):
    cod_anu = models.IntegerField(primary_key=True)
    ouverture_paiement = models.CharField(max_length=1, choices=(('O', 'Ouverte'), ('F', 'Fermé')), default=False)

    def __str__(self):
        return '{}/{}'.format(self.cod_anu, self.cod_anu+1)


@python_2_unicode_compatible
class SettingEtapePaiement(models.Model):
    etape = models.ForeignKey(Etape, related_name='settings_etape_paiement')
    cod_anu = models.IntegerField(default=2014)
    tarif = models.FloatField(null=True)
    demi_annee = models.BooleanField(default=False, help_text='peut s\'inscrire par semestre')
    nb_paiment_max = models.IntegerField(default=2)
    demi_tarif = models.BooleanField(default=False, help_text='demi tarif en cas de réins')

    def __str__(self):
        return '{} {}'.format(self.etape_id, self.cod_anu)

    def get_tarif_paiement(self, reins=False, semestre=False):
        tarif = self.tarif
        if self.demi_tarif and reins or semestre:
            tarif /= 2
        return tarif

@python_2_unicode_compatible
class Banque(models.Model):
    nom = models.CharField("Nom de la banque", max_length=100, unique=True)

    def _capitalize(self, field):
        return unicodedata.normalize('NFKD', unicode(field)).encode("ascii", "ignore").upper()

    def save(self, force_insert=False, force_update=False, using=None, **kwargs):
        if not self.id:
            self.id = Banque.objects.last().id + 1
        self.nom = self._capitalize(self.nom)
        return super(Banque, self).save(force_insert, force_update, using, **kwargs)

    def __str__(self):
        return unicode(self.nom)

    class Meta:
        db_table = u"pal_banque"
        verbose_name = u"banque"
        verbose_name_plural = u"banques"
        ordering = ['nom']


@python_2_unicode_compatible
class Bordereau(models.Model):
    """
    Bordereau
    Le bordereau qui contient les chèques ou les virements.
    """
    num_bordereau = models.IntegerField("Numéro bordereau")
    num_paiement = models.IntegerField(u"Numéro de paiement", blank=True, null=True)
    cloture = models.BooleanField(u"bordereau cloturé", default=False, blank=True)
    annee = models.ForeignKey(AnneeUniPaiement)
    date_cloture = models.DateField(u"Date de cloture du bordereau", blank=True, null=True)
    envoi_mail = models.BooleanField(u"envoie mail", default=False)
    objects = BordereauManager()
    auditeur = BordereauAuditeurManager()
    unfiltered = models.Manager()
    type_paiement = models.CharField('type de paiement du bordereau',
                                     choices=(('C', u'Chèque ordinaire'),
                                              ('B', u'Chèque de banque'),
                                              ('E', u"Chèque étranger"),
                                              ('V', u'Virement')),
                                     max_length=1)
    type_bordereau = models.CharField("type de bordereau", choices=(
        ('N', u'Normal'),
        ('A', u'Auditeur Libre')),
        default="N",
        max_length=1)
    comment = models.CharField(max_length=120, null=True, blank=True)

    def is_plein(self):
        volume = {
            'C': 200,
            'B': 1,
            'E': 1,
            'V': 200
        }
        if self.all_valid().count() >= volume[str(self.type_paiement)]:
            return True
        else:
            return False

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.cloture and not self.date_cloture:
            self.date_cloture = date.today()
            if not self.envoi_mail and not self.type_paiement == "V":
                self.send_mail_cloture_bordereau()
                if not settings.DEBUG:  # if in Production, send the mail
                    self.envoi_mail = True

        if not self.cloture and self.date_cloture:
            self.date_cloture = None
        super(Bordereau, self).save(force_insert, force_update, using, update_fields)

    def send_mail_cloture_bordereau(self):
        """
        Send confirmation mail to every paiementbackoffice's user.
        """
        context = {
            'date_cloture': self.date_cloture.strftime("%d-%m-%Y"),
        }
        template = Mail.objects.get(name='cloture_bordereau')
        idx = 0
        if self.type_bordereau == 'N':
            for p in self.paiementbackoffice_set.all():
                context.update({'nom_banque': p.nom_banque.nom,
                                'nom': p.etape.nom(),
                                'prenom': p.etape.prenom(),
                                'num_cheque': p.num_cheque,
                                'num_etu': p.etape.cod_ind.cod_etu,
                                'montant': p.somme,
                                'code_diplome': p.etape.cod_dip, })
                recipients = get_recipients(p.cod_ind, p.cod_anu.cod_anu)

                mail = template.make_message(recipients=recipients,
                                             context=context)
                if not idx % 100:  # we make a pause every 100 mails
                    time.sleep(1)

                mail.send()
                if settings.DEBUG:
                    # send only one mail in debug
                    break

                idx += 1
        else:
            for p in self.paiementauditeurbackoffice_set.all():
                context.update({
                    'nom_banque':  p.nom_banque.nom,
                    'nom': p.etape.nom(),
                    'prenom': p.etape.prenom(),
                    'num_cheque': p.num_cheque,
                    'num_etu': p.etape.cod_etu(),
                    'montant': p.somme,
                    'code_diplome': 'L1NPSY',
                })
                # recipients = get_recipients(p.etape.cod_ind, p.cod_anu.cod_anu)
                # recipients = (p.etape.cod_etu()+'@foad.iedparis8.net',)

                # mail = template.make_message(recipients=recipients,
                #                              context=context)
                if not idx % 100:  # we make a pause every 100 mails
                    time.sleep(1)

                # mail.send()
                if settings.DEBUG:
                    # send only one mail in debug
                    break

                idx += 1

    def total_sum(self):
        """
        Retourne la somme totale du bordereau courant.
        """
        return self.all_valid().aggregate(Sum('somme'))['somme__sum']

    def nb_cheque_total(self):
        """
        Retourne le nombre total de chèque dans le présent bordereau.
        """
        return self.all_valid().count()

    def all_valid(self):
        if self.type_bordereau == 'N':
            return self.paiementbackoffice_set.filter(type=self.type_paiement, etape__eta_iae='E') \
                                | self.paiementbackoffice_set.filter(
                                    type=self.type_paiement, etape__force_encaissement=True)
        else:
            return self.paiementauditeurbackoffice_set.all()

    def __str__(self):
        type_paiement = u"auditeur" if self.type_bordereau == "A" else "etudiant"
        return u"%s paiement %s bordereau %s" % (type_paiement, self.num_paiement, self.num_bordereau)

    class Meta:
        ordering = ['type_bordereau', 'num_paiement', 'num_bordereau']
        get_latest_by = 'num_bordereau'
        verbose_name = "Bordereau"
        verbose_name_plural = "Bordereaux"


@python_2_unicode_compatible
class PaiementBackoffice(models.Model):
    """ PaiementBackoffice
        C'est la class qui gére les paiements
    """
    etape = models.ForeignKey(InsAdmEtp, related_name="paiements", null=True)
    # cle primaire composite
    cod_anu = models.ForeignKey(AnneeUniPaiement, verbose_name=u"Code Annee Universitaire", null=True,
                                db_column='COD_ANU')
    cod_ind = models.ForeignKey(Individu, db_column='COD_IND', null=True)
    cod_etp = models.CharField(u"Code Etape", max_length=8, null=True,
                               db_column="COD_ETP")
    cod_vrs_vet = models.CharField(u"(COPIED)Numero Version Etape", max_length=3, db_column="COD_VRS_VET", null=True)
    num_occ_iae = models.CharField(u"", max_length=2, null=True, db_column="NUM_OCC_IAE")
    # fin
    type = models.CharField("type paiement", choices=(('C', u'Chèque'),
                                                      ('B', u'Chèque de banque'),
                                                      ('E', u"Chèque étranger"),
                                                      ('V', u'Virement')),
                            max_length=1)
    num_cheque = models.CharField("Numéro de chéque", max_length=30, null=True, blank=True)
    nom_banque = models.ForeignKey(Banque, null=True, blank=True, verbose_name=u"Nom de la banque")
    autre_payeur = models.CharField("Autre payeur", max_length=30, null=True, blank=True)
    somme = models.FloatField("Somme")
    date = models.DateField("date prévue", null=True, blank=True)
    date_virement = models.DateField("Date du virement effectué", null=True, blank=True)
    date_saisi = models.DateField(auto_now=True)
    bordereau = models.ForeignKey(Bordereau, verbose_name="Bordereau", null=True, blank=True)  # les bordereaux ne
    # concerne que les chèques
    is_not_ok = models.BooleanField(u"Impayé", default=False)
    num_paiement = models.IntegerField(u"Numéro de paiement", blank=True, null=True)
    observation = models.CharField(u"Observation", max_length=100, blank=True, null=True)
    objects = PaiementBackofficeManager()

    class Meta:
        db_table = u"pal_paiement_backoffice"
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"
        ordering = ['id']

    def __init__(self, *args, **kwargs):
        super(PaiementBackoffice, self).__init__(*args, **kwargs)
        self.__original_is_ok = self.is_not_ok

    def __str__(self):
        return str(self.num_paiement)

    def save(self, force_insert=False, force_update=False, using=None, **kwargs):
        if not self.cod_anu or not self.cod_ind or not self.cod_etp or not self.cod_vrs_vet:
            anu = AnneeUniPaiement.objects.get(cod_anu=self.etape.cod_anu.cod_anu)
            self.cod_anu = anu
            self.cod_ind = self.etape.cod_ind
            self.cod_etp = self.etape.cod_etp
            self.cod_vrs_vet = self.etape.cod_vrs_vet
            self.num_occ_iae = self.etape.num_occ_iae

        if not self.num_paiement:
            self.num_paiement = self.etape.paiements.count() + 1

        if not self.bordereau_id:  # il n'y a pas encore de bordereau attribuer
            self.bordereau = Bordereau.objects.last_bordereau(self.num_paiement, self.cod_anu.cod_anu, self.type)

        if self.__original_is_ok != self.is_not_ok:
            if self.is_not_ok:
                self.send_mail_relance()
            else:
                self.send_mail_regularisation()

            self.__original_is_ok = self.is_not_ok

        super(PaiementBackoffice, self).save(force_insert, force_update, using, **kwargs)

    def send_mail_relance(self):
        """
        """
        # Creation du contexte
        context = {
            "nom": self.etape.nom(),
            "prenom": self.etape.prenom(),
            "adresse": self.etape.adresse(),
            "cod_etu": self.etape.cod_ind.cod_etu,
            "cod_etp": self.etape.cod_etp,
            "num_paiement": self.num_paiement,
            "somme": self.somme,
        }
        pdf_file = TemplateHtmlModel.objects.get(name='mail_relance').get_pdf_file(context)
        template_mail = Mail.objects.get(name='mail_relance')
        recipients = get_recipients(self.cod_ind, self.cod_anu.cod_anu)

        mail = template_mail.make_message(recipients=recipients)
        mail.attach(filename='impaye.pdf', content=pdf_file)
        mail.send()

    def send_mail_regularisation(self):
        """
        """
        # Creation du contexte
        context = {
            "nom": self.etape.nom(),
            "prenom": self.etape.prenom(),
            "adresse": self.etape.adresse(),
            "cod_etu": self.etape.cod_ind.cod_etu,
            "cod_etp": self.etape.cod_etp,
        }
        pdf_file = TemplateHtmlModel.objects.get(name='mail_regularisation').get_pdf_file(context)
        template_mail = Mail.objects.get(name='mail_regularisation')
        recipients = get_recipients(self.cod_ind, self.cod_anu.cod_anu)

        mail = template_mail.make_message(recipients=recipients)
        mail.attach(filename='regularisation.pdf', content=pdf_file)
        mail.send()


@receiver(post_save, sender=PaiementBackoffice)
def update_total_and_reste(sender, **kwargs):
    instance = kwargs.get('instance', None)
    ct = CalculTarif.objects.get_or_create(etape=instance.etape)[0]
    etape_paiement = instance.etape
    etape_paiement.__class__ = InsAdmEtpPaiement
    ct.total = etape_paiement.get_total()
    ct.reste = etape_paiement.get_reste()
    ct.save()


class PaiementAuditeurBackoffice(models.Model):
    """ PaiementBackoffice
        C'est la class qui gére les paiements
    """
    etape = models.ForeignKey(AuditeurLibreApogee, related_name="paiements")
    cod_anu = models.ForeignKey(AnneeUniPaiement, verbose_name=u"Code Annee Universitaire", null=True,
                                db_column='COD_ANU')
    cod_etp = models.CharField(u"Code Etape", max_length=8, null=True,
                               db_column="COD_ETP")

    type = models.CharField("type paiement", choices=(('C', u'Chéque'),
                                                      ('B', u'Chèque de banque'),
                                                      ('E', u"Chèque étranger"),
                                                      ('V', u'Virement')),
                            max_length=1)
    num_cheque = models.CharField("Numéro de chéque", max_length=30, null=True, blank=True)
    nom_banque = models.ForeignKey(Banque, null=True, blank=True, verbose_name=u"Nom de la banque")
    autre_payeur = models.CharField("Autre payeur", max_length=30, null=True, blank=True)
    somme = models.FloatField("Somme")
    date = models.DateField("date prévue", null=True, blank=True)
    date_virement = models.DateField("Date du virement effectué", null=True, blank=True)
    date_saisi = models.DateField(auto_now=True)
    bordereau = models.ForeignKey(Bordereau, verbose_name="Bordereau", null=True, blank=True)  # les bordereaux ne
    # concerne que les chèques
    is_not_ok = models.BooleanField(u"Impayé", default=False)
    num_paiement = models.IntegerField(u"Numéro de paiement", blank=True, null=True)
    observation = models.CharField(u"Observation", max_length=100, blank=True, null=True)

    objects = PaiementBackofficeManager()

    class Meta:
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"

    def __unicode__(self):
        return str(self.num_paiement)

    def save(self, force_insert=False, force_update=False, using=None, **kwargs):
        if not self.cod_anu or not self.cod_etp:
            anu = AnneeUniPaiement.objects.get(cod_anu=self.etape.annee.cod_anu)
            self.cod_anu = anu
            self.cod_etp = 'L1NPSY'

        if not self.num_paiement:
            self.num_paiement = self.etape.paiements.count() + 1

        if not self.bordereau_id:  # il n'y a pas encore de bordereau attribuer
            self.bordereau = Bordereau.auditeur.last_bordereau(self.num_paiement, self.cod_anu.cod_anu, self.type)

        # if self.__original_is_ok != self.is_not_ok:
        #     if self.is_not_ok:
        #         self.send_mail_relance()
        #     else:
        #         self.send_mail_regularisation()
        #
        #     self.__original_is_ok = self.is_not_ok

        super(PaiementAuditeurBackoffice, self).save(force_insert, force_update, using, **kwargs)
#
#
# class BordereauAuditeur(Bordereau):
#     class Meta:
#         proxy = True
#         app_label = "backoffice"
#         verbose_name = "bordereau auditeur"
#         verbose_name_plural = "bordereaux auditeur"


class PaiementParInscription(models.Model):
    '''
    Table that contains the primary inscription of each student (or many inscriptions if he is double cursus)
    and the wish to which this inscription corresponds, as well as the payment info of what the student has payed
    '''
    # cle primaire composite
    cod_anu = models.CharField(max_length=4, null=True)
    cod_ind = models.CharField(max_length=10, null=True)
    cod_etp = models.CharField(u"Code Etape", max_length=8, null=True,
                               db_column="COD_ETP")
    cod_vrs_vet = models.CharField(u"(COPIED)Numero Version Etape", max_length=3, db_column="COD_VRS_VET", null=True)
    num_occ_iae = models.CharField(u"", max_length=2, null=True, db_column="NUM_OCC_IAE")
    # fin
    cod_etu = models.CharField(max_length=10)
    individu = models.ForeignKey(Individu2, null=True)
    wish = models.ForeignKey(Wish, null=True, unique=True)
    montant_paye = models.FloatField(null=True)
    paiment_type = models.CharField(u"Paiement Type", null=True, max_length=3)
    bordereau = models.IntegerField(null=True)




