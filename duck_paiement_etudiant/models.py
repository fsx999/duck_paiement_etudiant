# -*- coding: utf-8 -*-
import tempfile
from django.conf import settings

from django.db import models
import unicodedata
from django.db.models import Sum
from django.template import Template, Context
from django.template.loader import render_to_string
from django.utils.encoding import python_2_unicode_compatible
from mailrobot.models import MailBody, Mail
from duck_utils.utils import email_ied, get_recipients
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
        tarif = self.settings_etape_paiement.get_tarif_paiement(reins=self.is_reins(), semestre=self.demi_annee)
        if self.exoneration:
            if self.exoneration == 'T':
                tarif = 0
            elif self.exoneration == 'P':
                tarif /= 2.0
        total_payer = 0
        for x in self.paiements.filter(is_ok=False):
            total_payer += x.somme
        reste = tarif - total_payer
        return reste


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
        return self.paiementbackoffice_set.filter(type=self.type_paiement, etape__eta_iae='E') \
            | self.paiementbackoffice_set.filter(
            type=self.type_paiement, etape__force_encaissement=True)

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
        pdf_file = TemplateHtmlModel.objects.get(name='mail_relance').get_pdf(context)
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
        pdf_file = TemplateHtmlModel.objects.get(name='mail_regularisation').get_pdf(context)
        template_mail = Mail.objects.get(name='mail_regularisation')
        recipients = get_recipients(self.cod_ind, self.cod_anu.cod_anu)

        mail = template_mail.make_message(recipients=recipients)
        mail.attach(filename='regularisation.pdf', content=pdf_file)
        mail.send()


# class AuditeurLibreApogee(models.Model):
#     last_name = models.CharField("Nom", max_length=30)
#     first_name = models.CharField("Prenom", max_length=30)
#     personal_email = models.EmailField("email personnel", max_length=200)
#     address = models.CharField("adresse", max_length=200)
#     phone_number = models.CharField("numéro de téléphone", max_length=15, null=True, default=None)
#     code_ied = models.CharField('code ied', max_length=8)
#     status_modified = models.BooleanField(default=True)
#     access_claroline = models.BooleanField("Accès à claroline", default=True)
#     date_registration_current_year = models.DateField(auto_now_add=True)
#     birthday = models.DateField("Date de naissance")
#     annee = models.ForeignKey(AnneeUni)
#
#     def get_email(self, annee):
#         return self.personal_email
#     # def remontee_claroline(self, cours=None, envoi_mail=True, mail=None, email_perso=None):
#     #     etapes = ['L1NPSY']
#     #     user_foad = FoadUser.objects.using('foad').filter(username=str(self.code_ied))
#     #     if not user_foad.count():
#     #         user_foad = FoadUser.objects.using('foad').filter(username=self.code_ied)
#     #     if user_foad.count():
#     #         user_foad = user_foad[0]
#     #     else:
#     #         user_foad = FoadUser(username=self.code_ied)
#     #     if not self.code_ied:
#     #         raise Exception(u"Il n'y a pas de code étudiant")
#     #     user_foad.email = str(self.code_ied) + '@foad.iedparis8.net'
#     #     user_foad.nom = self.last_name
#     #     user_foad.prenom = self.first_name
#     #     user_foad.statut = 5
#     #     user_foad.official_code = self.code_ied
#     #     user_foad.password = make_ied_password(self.code_ied[:-1])
#     #     user_foad.save(using='foad')  # création de l'user
#     #     for e in etapes:
#     #         dips = FoadDip.objects.using('foad').filter(user_id=user_foad.user_id, dip_id=e)
#     #         if not dips.count():
#     #             FoadDip.objects.using('foad').create(user_id=user_foad.user_id, dip_id=e)
#     #         if cours:
#     #             for cour in cours[e]:
#     #                 t = FoadCourUser.objects.using('foad').get_or_create(user_id=user_foad.user_id,
#     #                                                                      code_cours=cour,
#     #                                                                      statut=5)
#     #     FoadCourUser.objects.using('foad').get_or_create(user_id=user_foad.user_id,
#     #                                                      code_cours="EEIED",
#     #                                                      statut=5)
#     #     FoadCourUser.objects.using('foad').get_or_create(user_id=user_foad.user_id,
#     #                                                      code_cours="RD",
#     #                                                      statut=5)
#     #     FoadCourUser.objects.using('foad').get_or_create(user_id=user_foad.user_id,
#     #                                                      code_cours="ISIED",
#     #                                                      statut=5)
#     #     new = FoadCourUser.objects.using('foad').get_or_create(user_id=user_foad.user_id,
#     #                                                            code_cours="EU",
#     #                                                            statut=5)[1]
#     #     if not CompteMail.objects.using('vpopmail').filter(pw_name=user_foad.username):
#     #         cod = user_foad.prenom.replace(" ", "\\ ").replace("'", "\\'") + '-' + user_foad.nom.replace(" ", "\\ ").replace("'", "\\'")
#     #         cod = unicodedata.normalize('NFKD', unicode(cod)).encode("ascii", "ignore").upper()
#     #         command = u'/home/ied-www/bin/vadduser  -q 500000000 -c "%s" %s %s' % (
#     #             cod,
#     #             user_foad.email,
#     #             user_foad.password
#     #         )
#     #
#     #         os.system(command)
#     #     if not email_perso:
#     #         email = [self.personal_email, user_foad.email] if not settings.DEBUG else ['paul.guichon@iedparis8.net']
#     #     else:
#     #         email = [email_perso]
#     #     if envoi_mail:
#     #         if not mail:
#     #             mail = Mail.objects.get(name='remontee')
#     #         message = mail.make_message(
#     #             recipients=email,
#     #             context={
#     #                 'etape': etapes[0],
#     #                 'prenom': user_foad.prenom,
#     #                 'username': user_foad.username,
#     #                 'password': user_foad.password,
#     #                 'email': user_foad.email,
#     #
#     #                 })
#     #         message.send()
#     #     self.status_modified = False
#     #     self.save()
#     #     return 1
#
#     def __unicode__(self):
#         return self.last_name + ' ' + self.first_name
#
#     class Meta:
#         db_table = u"auditeurs_libre"
#         verbose_name = u"auditeur libre"
#         verbose_name_plural = u"auditeurs libres"
#
#
# class PaiementAuditeurBackoffice(models.Model):
#     """ PaiementBackoffice
#         C'est la class qui gére les paiements
#     """
#     etape = models.ForeignKey(AuditeurLibreApogee, related_name="paiements")
#     type = models.CharField("type paiement", choices=(('C', u'Chéque'),
#                                                       ('B', u'Chèque de banque'),
#                                                       ('E', u"Chèque étranger"),
#                                                       ('V', u'Virement')),
#                             max_length=1)
#     num_cheque = models.CharField("Numéro de chéque", max_length=30, null=True, blank=True)
#     nom_banque = models.CharField("Nom de la banque", max_length=60, null=True, blank=True)
#     nom_banque_bis = models.ForeignKey(Banque, null=True, blank=True, verbose_name=u"Nom de la banque")
#     autre_payeur = models.CharField("Autre payeur", max_length=30, null=True, blank=True)
#     somme = models.FloatField("Somme")
#     date = models.DateField("date prévue", null=True, blank=True)
#     date_virement = models.DateField("Date du virement effectué", null=True, blank=True)
#     date_saisi = models.DateField(auto_now=True)
#     bordereau = models.ForeignKey(Bordereau, verbose_name="Bordereau", null=True, blank=True)  # les bordereaux ne
#     # concerne que les chèques
#     is_not_ok = models.BooleanField(u"Impayé", default=False)
#     num_paiement = models.IntegerField(u"Numéro de paiement", blank=True, null=True)
#     observation = models.CharField(u"Observation", max_length=100, blank=True, null=True)
#
#     class Meta:
#         db_table = u"pal_paiement_auditeur_backoffice"
#         verbose_name = "Paiement"
#         verbose_name_plural = "Paiements"
#
#     def __unicode__(self):
#         return str(self.num_paiement)
#
#     def save(self, force_insert=False, force_update=False, using=None):
#         if not self.num_paiement:
#             self.num_paiement = self.etape.paiements.count() + 1
#         if self.type == 'C':  # il s'aggit d'un chèque
#             if not self.bordereau_id:  # il n'y a pas encore de bordereau attribuer
#                 self.bordereau = Bordereau.auditeur.last_bordereau(self.num_paiement)
#
#         super(PaiementAuditeurBackoffice, self).save(force_insert, force_update, using)
#
#
# class BordereauAuditeur(Bordereau):
#     class Meta:
#         proxy = True
#         app_label = "backoffice"
#         verbose_name = "bordereau auditeur"
#         verbose_name_plural = "bordereaux auditeur"
