# coding=utf-8
from django.db import models
from django_apogee.models import AnneeUni
__author__ = 'paul'


class BordereauManager(models.Manager):

    def get_query_set(self):
        return super(BordereauManager, self).get_query_set().filter(type_bordereau='N')

    def last_bordereau(self, num_paiement, annee, type_paiement):
        try:

            last_bordereau = self.filter(num_paiement=num_paiement, annee=annee, type_paiement=type_paiement).latest()
            if last_bordereau.cloture or last_bordereau.is_plein():
                return self.create(num_paiement=num_paiement,
                                   num_bordereau=last_bordereau.num_bordereau + 1,
                                   type_paiement=type_paiement,
                                   annee_id=annee)
            else:
                return last_bordereau
        except models.ObjectDoesNotExist:  # Si c'est le premier on crée
            return self.create(num_paiement=num_paiement, num_bordereau=1, annee_id=annee, type_paiement=type_paiement)


class BordereauAuditeurManager(BordereauManager):

    def get_query_set(self):
        return super(BordereauAuditeurManager, self).get_query_set().filter(type_bordereau='A')

    # def last_bordereau(self, num_paiement):
    #     try:
    #         from inscription.models.individu_models import AnneeEnCour
    #         annee = AnneeEnCour.objects.get(annee_en_cours=True).annee
    #         year = AnneeUni.objects.get(cod_anu=annee)
    #         last_bordereau = self.filter(num_paiement=num_paiement, annee=year).latest()
    #         if last_bordereau.cloture or last_bordereau.is_plein():
    #             return self.create(num_paiement=num_paiement,
    #                                num_bordereau=last_bordereau.num_bordereau + 1,
    #                                annee=year)
    #         else:
    #             return last_bordereau
    #     except models.ObjectDoesNotExist:  # Si c'est le premier on crée
    #         return self.create(num_paiement=num_paiement, num_bordereau=1, type_bordereau='A')
