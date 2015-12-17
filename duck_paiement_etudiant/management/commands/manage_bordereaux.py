from django.core.management import BaseCommand
from django.db.models import Max
from duck_paiement_etudiant.models import PaiementParInscription
from duck_paiement_etudiant.utils import save_worksheet


def create_bordereau():
    max_bordereau = PaiementParInscription.objects.all().aggregate(Max('bordereau'))

    max_bor = max_bordereau['bordereau__max']
    print max_bor

    if not max_bor:
        max_bor = 1
    else:
        max_bor += 1
    print max_bor
    PaiementParInscription.objects.filter(wish__isnull=False, montant_paye__isnull=False, paiment_type='CB')\
        .update(bordereau=max_bor)


def imprimer_bordereau(bordereau_number):
    bordereaux = PaiementParInscription.objects.filter(bordereau=bordereau_number)

    data = []
    for ins in bordereaux:
        data.append([ins.cod_etu, ins.montant_paye])

    filename = 'bordereau_{}.xls'.format(bordereau_number)
    save_worksheet(filename, data)


class Command(BaseCommand):
    def handle(self, *args, **options):
        # create_bordereau()
        imprimer_bordereau(1)
