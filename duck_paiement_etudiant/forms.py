# -*- coding: utf-8 -*-
from django.core.exceptions import ValidationError
from django.forms import ModelForm
from duck_paiement_etudiant.models import PaiementBackoffice


class PaiementBackofficeForm(ModelForm):
    class Meta:
        model = PaiementBackoffice

    def clean(self):
        if self.cleaned_data['type'] in ['C', 'B', 'E']: # type chèque
            error_list = []
            if not self.cleaned_data.get('num_cheque', '').strip():
                error_list.append(ValidationError("Un chèque doit avoir un numéro de chèque associé.",
                                                  code='missing_num_cheque'))

            if not self.cleaned_data.get('nom_banque', None):
                error_list.append(ValidationError("Un chèque doit avoir une banque associée.",
                                                  code='missing_nom_banque'))

            if error_list:
                raise ValidationError(error_list)

        if self.cleaned_data['type'] == 'V': # type virement
            if not self.cleaned_data.get('date', None): # date prévue
                raise ValidationError("Un virement doit avoir une date prévue pour être valide.",
                                      code='missing_date')

        return self.cleaned_data
