# -*- coding: utf-8 -*-
from django.db import models
import unicodedata
from .managers import BordereauManager, BordereauAuditeurManager
from django_apogee.models import InsAdmEtp as INS_ADM_ETP_IED, AnneeUni, Individu as INDIVIDU


class Banque(models.Model):
    nom = models.CharField("Nom de la banque", max_length=100, unique=True)

    def _capitalize(self, field):
        return unicodedata.normalize('NFKD', unicode(field)).encode("ascii", "ignore").upper()

    def save(self, force_insert=False, force_update=False, using=None):
        self.nom = self._capitalize(self.nom)
        return super(Banque, self).save(force_insert, force_update, using)

    def __unicode__(self):
        return unicode(self.nom)

    class Meta:
        db_table = u"pal_banque"
        verbose_name = u"banque"
        verbose_name_plural = u"banques"
        ordering = ['nom']


class Bordereau(models.Model):
    """ Bordereau
    Le bordreau qui contient les chèques français.
    """
    num_bordereau = models.IntegerField("Numéro bordereau")
    num_paiement = models.IntegerField(u"Numéro de paiement", blank=True, null=True)
    cloture = models.BooleanField(u"bordereau cloturé", default=False, blank=True)
    annee = models.ForeignKey(AnneeUni, default=2012)
    date_cloture = models.DateField(u"Date de cloture du bordereau", blank=True, null=True)
    envoi_mail = models.BooleanField(u"envoie mail", default=False)
    objects = BordereauManager()
    auditeur = BordereauAuditeurManager()
    type_bordereau = models.CharField("type de bordereau", choices=(
        ('N', u'Normal'),
        ('A', u'Auditeur Libre')),
        default="N",
        max_length=1)

    def is_plein(self):
        if self.all_valid().count() >= 200:
            return True
        else:
            return False

    def impression_bordereu(self, flux, annee):
    #     RED = 10
    #     GRIS = 22
    #
    #     COL_NUM_CHEQUE = 1
    #     COL_NOM_BANQUE = 2
    #     COL_NOM_ETUDIANT = 3
    #     COL_PRENOM_ETUDIANT = 4
    #     COL_CODE_ETUDIANT = 5
    #     COL_SOMME = 6
    #     COL_AUTRE_PAYEUR = 7
    #     COL_DATE_CLOTURE = 7
    #     all_border = 'borders: left thick, right thick, top thick, bottom thick;'
    #     gris = 'pattern: pattern solid, pattern_fore_colour 22;'
    #     center = 'alignment: horizontal center;'
    #     gauche = "alignment: horizontal left;"
    #     bold = "font: bold True;"
    #     size = "font: height 250;"
    #     book = xlwt.Workbook(encoding='utf-8')
    #     row = 0
    #     feuille = book.add_sheet('Bordereau')
    #     feuille.portrait = False
    #     feuille.top_margin = 0.5
    #     feuille.bottom_margin = 0.5
    #     feuille.write_merge(row, row, 0, 4, u"I.E.D. Frais  d'Enseignement à Distance  %s/%s" % (
    #         annee,
    #         int(annee) + 1),
    #         xlwt.Style.easyxf(bold))
    #     row += 2
    #     feuille.write_merge(row, row, 0, 4, "MODE DE PAIEMENT : CHÈQUES NORMAUX",
    #                         xlwt.Style.easyxf(bold))
    #
    #     row += 1
    #     feuille.write_merge(row, row, 0, 4, "Paiement numéro %s / Bordereau Numéro : %s" % (
    #         self.num_paiement,
    #         self.num_bordereau))
    #     feuille.col(0).width = 1250
    #     feuille.col(COL_NUM_CHEQUE).width = 2900
    #     feuille.col(COL_NOM_BANQUE).width = 6250
    #     feuille.col(COL_NOM_ETUDIANT).width = 6250
    #     feuille.col(COL_PRENOM_ETUDIANT).width = 5000
    #     feuille.col(COL_CODE_ETUDIANT).width = 2875
    #     feuille.col(COL_SOMME).width = 3000
    #     feuille.col(COL_AUTRE_PAYEUR).width = 8000
    #
    #     row += 2
    #     entete = gris + center + all_border + 'alignment: vertical center;' + bold
    #     feuille.write(row, COL_NUM_CHEQUE, u"N° CHEQUE", xlwt.Style.easyxf(entete))
    #     feuille.write(row, COL_NOM_BANQUE, u"BANQUE", xlwt.Style.easyxf(entete))
    #     feuille.write(row, COL_NOM_ETUDIANT, u"NOM ETUDIANT", xlwt.Style.easyxf(entete))
    #     feuille.write(row, COL_PRENOM_ETUDIANT, u"PRENOM ETUDIANT", xlwt.Style.easyxf(entete))
    #     feuille.write(row, COL_CODE_ETUDIANT, u"CODE ETUDIANT", xlwt.Style.easyxf(entete))
    #     feuille.write(row, COL_SOMME, u"€", xlwt.Style.easyxf(entete))
    #     feuille.write(row, COL_AUTRE_PAYEUR, u"PAYEUR – TITULAIRE DU COMPTE", xlwt.Style.easyxf(entete))
    #     if self.type_bordereau == 'N':
    #         paiements = self.all_valid().order_by('nom_banque_bis__nom', 'somme', 'pk')
    #     else:
    #         paiements = self.paiementauditeurbackoffice_set.all().order_by('nom_banque_bis__nom', 'somme', 'pk')
    #
    #     nb_paiement = len(paiements)
    #
    #     for i, p in enumerate(paiements):
    #         value = 'borders: left thick, right thick; pattern: pattern solid, pattern_fore_colour %s;' % (
    #             GRIS if i % 2 else 100)
    #
    #         if i == 0:
    #             value += 'borders: left thick, right thick, top thick;'
    #         if i + 1 == nb_paiement:
    #             value += 'borders: left thick, right thick, bottom thick;'
    #         row += 1
    #         if self.type_bordereau == 'N':
    #             etudiant = p.etape.COD_IND
    #         else:
    #             etudiant = p.etape
    #             etudiant.LIB_NOM_PAT_IND = etudiant.last_name
    #             etudiant.LIB_PR1_IND = etudiant.first_name
    #             etudiant.COD_ETU = etudiant.code_ied
    #
    #         try:
    #             nom_banque = p.nom_banque_bis.nom
    #         except AttributeError:
    #             nom_banque = u"Annomalie"
    #             value = 'borders: left thick, right thick;pattern: pattern solid, pattern_fore_colour %s;' % RED
    #         feuille.write(row, 0, i + 1, xlwt.Style.easyxf(value + center))
    #         feuille.write(row, COL_NUM_CHEQUE, p.num_cheque, xlwt.Style.easyxf(value + center))
    #         feuille.write(row, COL_NOM_BANQUE, nom_banque, xlwt.Style.easyxf(value))
    #         feuille.write(row, COL_NOM_ETUDIANT, etudiant.LIB_NOM_PAT_IND, xlwt.Style.easyxf(value))
    #         feuille.write(row, COL_PRENOM_ETUDIANT, etudiant.LIB_PR1_IND, xlwt.Style.easyxf(value))
    #         feuille.write(row, COL_CODE_ETUDIANT, etudiant.COD_ETU, xlwt.Style.easyxf(value + gauche))
    #         feuille.write(row, COL_SOMME, p.somme, xlwt.Style.easyxf(value))
    #         feuille.write(row, COL_AUTRE_PAYEUR, p.autre_payeur, xlwt.Style.easyxf(value))
    #     row += 2
    #     total = all_border + bold + size
    #     feuille.row(row).height = 500
    #     feuille.write(row, COL_SOMME - 1, u'Total :',
    #                   xlwt.Style.easyxf(total))
    #     if self.type_bordereau == 'N':
    #         feuille.write(row, COL_SOMME, self.all_valid().aggregate(Sum('somme'))['somme__sum'],
    #                   xlwt.Style.easyxf(total))
    #     else:
    #         feuille.write(row, COL_SOMME,  self.paiementauditeurbackoffice_set.all().aggregate(Sum('somme'))['somme__sum'],
    #                   xlwt.Style.easyxf(total))
    #     date1 = self.date_cloture.strftime('%d/%m/%Y') if self.date_cloture else "Non cloturé"
    #     row += 2
    #     feuille.row(row).height = 500
    #     feuille.write_merge(row, row, COL_DATE_CLOTURE - 2,  COL_DATE_CLOTURE - 1, u'Date de remise :',
    #                         xlwt.Style.easyxf(total))
    #     feuille.write(row, COL_DATE_CLOTURE, date1,
    #                   xlwt.Style.easyxf(total))
    #
    #     book.save(flux)
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
        pass

    def all_valid(self):
        return self.paiementbackoffice_set.filter(type="C", etape__ETA_IAE='E') | self.paiementbackoffice_set.filter(
            type="C", etape__force_encaissement=True)

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
    etape = models.ForeignKey(INS_ADM_ETP_IED, related_name="paiements")
    # cle primaire composite
    cod_anu = models.ForeignKey(AnneeUni, verbose_name=u"Code Annee Universitaire", null=True)
    cod_ind = models.ForeignKey(INDIVIDU, db_column='COD_IND', null=True)
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
    nom_banque = models.CharField("Nom de la banque", max_length=60, null=True, blank=True)
    nom_banque_bis = models.ForeignKey(Banque, null=True, blank=True, verbose_name=u"Nom de la banque")
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

    class Meta:
        db_table = u"pal_paiement_backoffice"
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"

    def __init__(self, *args, **kwargs):
        super(PaiementBackoffice, self).__init__(*args, **kwargs)
        self.__original_is_ok = self.is_ok

    def __unicode__(self):
        return str(self.num_paiement)

    def save(self, force_insert=False, force_update=False, using=None):
        if not self.num_paiement:
            self.num_paiement = self.etape.paiements.count() + 1
        if self.type == 'C':  # il s'aggit d'un chèque                    x
            if not self.bordereau_id:  # il n'y a pas encore de bordereau attribuer
                self.bordereau = Bordereau.objects.last_bordereau(self.num_paiement)

        if self.__original_is_ok != self.is_ok:
            pass
        if not self.cod_anu:
            self.cod_anu = self.etape.COD_ANU
            self.cod_ind = self.etape.COD_IND
            self.cod_etp = self.etape.COD_ETP
            self.cod_vrs_vet = self.etape.COD_VRS_VET
            self.num_occ_iae = self.etape.NUM_OCC_IAE
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


class AuditeurLibreApogee(models.Model):
    last_name = models.CharField("Nom", max_length=30)
    first_name = models.CharField("Prenom", max_length=30)
    personal_email = models.EmailField("email personnel", max_length=200)
    address = models.CharField("adresse", max_length=200)
    phone_number = models.CharField("numéro de téléphone", max_length=15, null=True, default=None)
    code_ied = models.CharField('code ied', max_length=8)
    status_modified = models.BooleanField(default=True)
    access_claroline = models.BooleanField("Accès à claroline", default=True)
    date_registration_current_year = models.DateField(auto_now_add=True)
    birthday = models.DateField("Date de naissance")
    annee = models.ForeignKey(AnneeUni)

    # def remontee_claroline(self, cours=None, envoi_mail=True, mail=None, email_perso=None):
    #     etapes = ['L1NPSY']
    #     user_foad = FoadUser.objects.using('foad').filter(username=str(self.code_ied))
    #     if not user_foad.count():
    #         user_foad = FoadUser.objects.using('foad').filter(username=self.code_ied)
    #     if user_foad.count():
    #         user_foad = user_foad[0]
    #     else:
    #         user_foad = FoadUser(username=self.code_ied)
    #     if not self.code_ied:
    #         raise Exception(u"Il n'y a pas de code étudiant")
    #     user_foad.email = str(self.code_ied) + '@foad.iedparis8.net'
    #     user_foad.nom = self.last_name
    #     user_foad.prenom = self.first_name
    #     user_foad.statut = 5
    #     user_foad.official_code = self.code_ied
    #     user_foad.password = make_ied_password(self.code_ied[:-1])
    #     user_foad.save(using='foad')  # création de l'user
    #     for e in etapes:
    #         dips = FoadDip.objects.using('foad').filter(user_id=user_foad.user_id, dip_id=e)
    #         if not dips.count():
    #             FoadDip.objects.using('foad').create(user_id=user_foad.user_id, dip_id=e)
    #         if cours:
    #             for cour in cours[e]:
    #                 t = FoadCourUser.objects.using('foad').get_or_create(user_id=user_foad.user_id,
    #                                                                      code_cours=cour,
    #                                                                      statut=5)
    #     FoadCourUser.objects.using('foad').get_or_create(user_id=user_foad.user_id,
    #                                                      code_cours="EEIED",
    #                                                      statut=5)
    #     FoadCourUser.objects.using('foad').get_or_create(user_id=user_foad.user_id,
    #                                                      code_cours="RD",
    #                                                      statut=5)
    #     FoadCourUser.objects.using('foad').get_or_create(user_id=user_foad.user_id,
    #                                                      code_cours="ISIED",
    #                                                      statut=5)
    #     new = FoadCourUser.objects.using('foad').get_or_create(user_id=user_foad.user_id,
    #                                                            code_cours="EU",
    #                                                            statut=5)[1]
    #     if not CompteMail.objects.using('vpopmail').filter(pw_name=user_foad.username):
    #         cod = user_foad.prenom.replace(" ", "\\ ").replace("'", "\\'") + '-' + user_foad.nom.replace(" ", "\\ ").replace("'", "\\'")
    #         cod = unicodedata.normalize('NFKD', unicode(cod)).encode("ascii", "ignore").upper()
    #         command = u'/home/ied-www/bin/vadduser  -q 500000000 -c "%s" %s %s' % (
    #             cod,
    #             user_foad.email,
    #             user_foad.password
    #         )
    #
    #         os.system(command)
    #     if not email_perso:
    #         email = [self.personal_email, user_foad.email] if not settings.DEBUG else ['paul.guichon@iedparis8.net']
    #     else:
    #         email = [email_perso]
    #     if envoi_mail:
    #         if not mail:
    #             mail = Mail.objects.get(name='remontee')
    #         message = mail.make_message(
    #             recipients=email,
    #             context={
    #                 'etape': etapes[0],
    #                 'prenom': user_foad.prenom,
    #                 'username': user_foad.username,
    #                 'password': user_foad.password,
    #                 'email': user_foad.email,
    #
    #                 })
    #         message.send()
    #     self.status_modified = False
    #     self.save()
    #     return 1

    def __unicode__(self):
        return self.last_name + ' ' + self.first_name

    class Meta:
        db_table = u"auditeurs_libre"
        verbose_name = u"auditeur libre"
        verbose_name_plural = u"auditeurs libres"


class PaiementAuditeurBackoffice(models.Model):
    """ PaiementBackoffice
        C'est la class qui gére les paiements
    """
    etape = models.ForeignKey(AuditeurLibreApogee, related_name="paiements")
    type = models.CharField("type paiement", choices=(('C', u'Chéque'),
                                                      ('B', u'Chèque de banque'),
                                                      ('E', u"Chèque étranger"),
                                                      ('V', u'Virement')),
                            max_length=1)
    num_cheque = models.CharField("Numéro de chéque", max_length=30, null=True, blank=True)
    nom_banque = models.CharField("Nom de la banque", max_length=60, null=True, blank=True)
    nom_banque_bis = models.ForeignKey(Banque, null=True, blank=True, verbose_name=u"Nom de la banque")
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

    class Meta:
        db_table = u"pal_paiement_auditeur_backoffice"
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"

    def __unicode__(self):
        return str(self.num_paiement)

    def save(self, force_insert=False, force_update=False, using=None):
        if not self.num_paiement:
            self.num_paiement = self.etape.paiements.count() + 1
        if self.type == 'C':  # il s'aggit d'un chèque
            if not self.bordereau_id:  # il n'y a pas encore de bordereau attribuer
                self.bordereau = Bordereau.auditeur.last_bordereau(self.num_paiement)

        super(PaiementAuditeurBackoffice, self).save(force_insert, force_update, using)


class BordereauAuditeur(Bordereau):
    class Meta:
        proxy = True
        app_label = "backoffice"
        verbose_name = "bordereau auditeur"
        verbose_name_plural = "bordereaux auditeur"
