# coding=utf-8
from django.db import models
from django_apogee.models import AnneeUni
__author__ = 'paul'



class BordereauManager(models.Manager):
    type_bordereau = 'N'

    def get_queryset(self):
        return super(BordereauManager, self).get_queryset().filter(type_bordereau=self.type_bordereau)

    def by_year(self, year):
        return self.filter(annee__cod_anu=year, type_bordereau=self.type_bordereau)

    def last_bordereau(self, num_paiement, annee, type_paiement):
        try:

            last_bordereau = self.filter(type_bordereau=self.type_bordereau, num_paiement=num_paiement, annee=annee, type_paiement=type_paiement).latest()
            if last_bordereau.cloture or last_bordereau.is_plein():
                return self.create(type_bordereau=self.type_bordereau,
                                   num_paiement=num_paiement,
                                   num_bordereau=last_bordereau.num_bordereau + 1,
                                   type_paiement=type_paiement,
                                   annee_id=annee)
            else:
                return last_bordereau
        except models.ObjectDoesNotExist:  # Si c'est le premier on crée
            return self.create(type_bordereau=self.type_bordereau, num_paiement=num_paiement, num_bordereau=1, annee_id=annee, type_paiement=type_paiement)


class BordereauAuditeurManager(BordereauManager):
    type_bordereau = 'A'



class PaiementBackofficeManager(models.Manager):
    def by_year(self, year):
        return self.filter(cod_anu=year)