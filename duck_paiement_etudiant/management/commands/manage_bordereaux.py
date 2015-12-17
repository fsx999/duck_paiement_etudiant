from django.core.management import BaseCommand
from django.db.models import Max
from duck_paiement_etudiant.models import PaiementParInscription


def create_bordereau():
    max_bordereau = PaiementParInscription.objects.all().aggregate(Max('bordereau'))

    max = max_bordereau['bordereau__max']
    print max

    if not max:
        max = 1
    else:
        max += 1
    print max
    PaiementParInscription.objects.filter(wish__isnull=False, montant_paye__isnull=False, paiment_type='CB')\
        .update(bordereau=max)


def imprimer_bordereau():
    pass

class Command(BaseCommand):
    def handle(self, *args, **options):
        create_bordereau()
