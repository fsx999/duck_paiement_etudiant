from django.core.management.base import BaseCommand
from duck_paiement_etudiant.models import PaiementBackoffice


class Command(BaseCommand):
    help = "My shiny new management command."

    def handle(self, *args, **options):

        for x in PaiementBackoffice.objects.filter(cod_anu=2014, is_not_ok=True):
            x.send_mail_relance()