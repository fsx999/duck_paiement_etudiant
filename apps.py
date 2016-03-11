# coding=utf-8
from django.apps import AppConfig


class DuckPaiementEtudiant(AppConfig):
    name = "duck_paiement_etudiant"
    label = "duck_paiement_etudiant"

    collapse_settings = [{
        "group_label": "Duck_Paiement_Etudiant",
        "icon": 'fa-fw fa fa-circle-o',
        "entries": [{
            "label": 'Banques ',
            "icon": 'fa-fw fa fa-circle-o',
            "url": '/duck_paiement_etudiant/banque/',  # name or url
            "groups_permissions": [],  # facultatif
            "permissions": [],  # facultatif
        }, {
            "label": 'Setting etape paiements ',
            "icon": 'fa-fw fa fa-circle-o',
            "url": '/duck_paiement_etudiant/settingetapepaiement/',  # name or url
            "groups_permissions": [],  # facultatif
            "permissions": [],  # facultatif
        }],

        "groups_permissions": [],  # facultatif
        "permissions": [],  # facultatif
    }, ]