# -*- coding: utf-8 -*-

from django.db import models
import unicodedata
from django.db.models import Sum
from django.utils.encoding import python_2_unicode_compatible
from mailrobot.models import MailBody
from .managers import BordereauManager, BordereauAuditeurManager, PaiementBackofficeManager
from django_apogee.models import InsAdmEtp, AnneeUni, Individu
from datetime import date

@python_2_unicode_compatible
class AnneeUniPaiement(models.Model):
    cod_anu = models.IntegerField(primary_key=True)
    ouverture_paiement = models.CharField(max_length=1, choices=(('O', 'Ouverte'), ('F', 'Fermé')), default=False)

    def __str__(self):
        return '{}/{}'.format(self.cod_anu, self.cod_anu+1)


@python_2_unicode_compatible
class Banque(models.Model):
    nom = models.CharField("Nom de la banque", max_length=100, unique=True)

    def _capitalize(self, field):
        return unicodedata.normalize('NFKD', unicode(field)).encode("ascii", "ignore").upper()

    def save(self, force_insert=False, force_update=False, using=None):
        self.nom = self._capitalize(self.nom)
        return super(Banque, self).save(force_insert, force_update, using)

    def __str__(self):
        return unicode(self.nom)

    class Meta:
        db_table = u"pal_banque"
        verbose_name = u"banque"
        verbose_name_plural = u"banques"
        ordering = ['nom']


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
        if not self.cloture and self.date_cloture:
            self.date_cloture = None
        super(Bordereau, self).save(force_insert, force_update, using, update_fields)

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


    #
    # def get_annee(self):
    #     return u"%s / %s" % (self.annee.cod_anu, int(self.annee.cod_anu) + 1)
    # get_annee.short_description = u"Année"
    #
    # def save(self, force_insert=False, force_update=False, using=None):
    #     if self.cloture and not self.date_cloture:
    #         self.date_cloture = date.today()
    #     if self.cloture and not self.envoi_mail:
    #         self.do_envoi_mail()
    #     return super(Bordereau, self).save(force_insert, force_update, using)
    #
    # def do_envoi_mail(self):
    #     for paiement in self.paiementbackoffice_set.all():
    #         etu = paiement.etape.COD_IND
    #         etape = paiement.etape
    #         text = u"""
    # %(nom)s %(prenom)s %(num_etu)s %(code_diplome)s
    #
    # Madame, Monsieur,
    # Nous vous adresserons ce e-mail informant que votre chèque numéro %(num_cheque)s de la banque %(nom_banque)s
    # d'un montant de %(montant)i euro vient d'être traiter par  nos service en date du %(date_cloture)s .
    # Il sera donc bientôt débiter de votre compte bancaire. \n
    # Nous vous prions de faire le nécessaire afin d'approvisionner votre compte, pour éviter tout désagrément de
    # paiement. \n
    # Nous vous prions d'agréer, Madame, Monsieur, nos cordiales salutations. \n
    #
    # PÔLE FINANCIER
    # Institut d’Enseignement à Distance – IED
    # UNIVERSITÉ PARIS 8
    # 2, rue de la Liberté
    # 93 526 SAINT-DENIS Cedex 02
    # \n
    # ne pas répondre à ce mail
    #         """ % {
    #             'nom': etu.LIB_NOM_PAT_IND,
    #             'prenom': etu.LIB_PR1_IND,
    #             'num_etu': etu.COD_ETU,
    #             'code_diplome': etape.COD_ETP,
    #             'num_cheque': paiement.num_cheque,
    #             'nom_banque': paiement.nom_banque,
    #             'montant': paiement.somme,
    #             'date_cloture': self.date_cloture.strftime("%d-%m-%Y")
    #         }
    #         send_mail(u"Chéque mis en encaissement", text, "nepasrepondre@iedparis8.net",
    #                   [etu.email_ied(), etu.get_email()])
    #     self.envoi_mail = True
    #     self.save()


    def all_valid(self):
        return self.paiementbackoffice_set.filter(type=self.type_paiement, etape__eta_iae='E') | self.paiementbackoffice_set.filter(
            type=self.type_paiement, etape__force_encaissement=True)

    def __unicode__(self):
        type_paiement = u"auditeur" if self.type_bordereau == "A" else "etudiant"
        return u"%s paiement %s bordereau %s" % (type_paiement, self.num_paiement, self.num_bordereau)

    class Meta:
        ordering = ['type_bordereau', 'num_paiement', 'num_bordereau']
        get_latest_by = 'num_bordereau'
        verbose_name = "Bordereau"
        verbose_name_plural = "Bordereaux"


class PaiementBackoffice(models.Model):
    """ PaiementBackoffice
        C'est la class qui gére les paiements
    """
    etape = models.ForeignKey(InsAdmEtp, related_name="paiements", null=True)
    # cle primaire composite
    cod_anu = models.ForeignKey(AnneeUniPaiement, verbose_name=u"Code Annee Universitaire", null=True, db_column='COD_ANU')
    cod_ind = models.ForeignKey(Individu, db_column='COD_IND', null=True)
    cod_etp = models.CharField(u"Code Etape", max_length=8, null=True,
                               db_column="COD_ETP")
    cod_vrs_vet = models.CharField(u"(COPIED)Numero Version Etape", max_length=3, db_column="COD_VRS_VET", null=True)
    num_occ_iae = models.CharField(u"", max_length=2, null=True, db_column="NUM_OCC_IAE")
    # fin
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
    is_ok = models.BooleanField(u"Impayé", default=False)
    num_paiement = models.IntegerField(u"Numéro de paiement", blank=True, null=True)
    observation = models.CharField(u"Observation", max_length=100, blank=True, null=True)
    objects = PaiementBackofficeManager()

    class Meta:
        db_table = u"pal_paiement_backoffice"
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"

    def __init__(self, *args, **kwargs):
        super(PaiementBackoffice, self).__init__(*args, **kwargs)
        self.__original_is_ok = self.is_ok

    def __unicode__(self):
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

        if self.__original_is_ok != self.is_ok:
            pass

        super(PaiementBackoffice, self).save(force_insert, force_update, using)

    # def envoi_mail_relance(self):
    #
    #     texte = u"""
    #     Vous trouverez en pièce jointe un rappel de paiement.
    #     """
    #     template = "impayer/impaye_pdf.html"
    #     objects = u"[IED] defaut de paiement des frais et droits de scolarité - IED annee universitaire 2012/2013."
    #     individu = self.etape.COD_IND
    #     f = open('impayer.pdf', 'wb')
    #     context = {'static': os.path.join(PROJECT_DIR, 'documents/static/images/').replace('\\', '/')}
    #     context['individu'] = individu
    #     context['etape'] = self.etape
    #     context['paiement'] = self
    #     pisa.CreatePDF(render_to_string(template, context), f)
    #     f.close()
    #     email = EmailMessage(subject=objects, body=texte, from_email='nepasrepondre@iedparis8.net',
    #                          to=[individu.get_email(), individu.email_ied(), 'nepasrepondre@iedparis8.net'])
    #                          # to=['nepasrepondre@iedparis8.net'])
    #                          # to=['nepasrepondre@iedparis8.net', 'evin.bayartan@iedparis8.net'])
    #
    #     f = open('impayer.pdf', 'r')
    #     email.attach(filename='impayer.pdf', content=f.read())
    #     email.send()
    #     f.close()
    #
    # def envoi_mail_regularisation(self):
    #     texte = u"""
    #     Vous trouverez en pièce jointe la confirmation de votre régulation.
    #     """
    #     template = "impayer/regulation_pdf.html"
    #     objects = u"[IED] defaut de paiement des frais et droits de scolarité - IED annee universitaire 2012/2013."
    #     individu = self.etape.COD_IND
    #     f = open('regularisation.pdf', 'wb')
    #     context = {'static': os.path.join(PROJECT_DIR, 'documents/static/images/').replace('\\', '/')}
    #     context['individu'] = individu
    #     context['etape'] = self.etape
    #     context['paiement'] = self
    #     pisa.CreatePDF(render_to_string(template, context), f)
    #     f.close()
    #     email = EmailMessage(subject=objects, body=texte, from_email='nepasrepondre@iedparis8.net',
    #                          to=[individu.get_email(), individu.email_ied(), 'nepasrepondre@iedparis8.net'])
    #                          # to=['nepasrepondre@iedparis8.net'])
    #
    #     f = open('regularisation.pdf', 'r')
    #     email.attach(filename='regularisation.pdf', content=f.read())
    #     email.send()
    #     f.close()


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
#     is_ok = models.BooleanField(u"Impayé", default=False)
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
