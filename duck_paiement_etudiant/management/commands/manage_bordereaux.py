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
    PaiementParInscription.objects.filter(wish__isnull=False, montant_paye__isnull=False, bordereau__isnull=True, paiment_type='CB')\
        .update(bordereau=max_bor)


def imprimer_bordereau(bordereau_number):
    bordereaux = PaiementParInscription.objects.filter(bordereau=bordereau_number)
    if bordereaux.count():
        print 'Printing bordereau {}'.format(bordereau_number)
        total = 0
        data = [['#', 'Numero de commande', 'Nom', 'Prenom', 'Code etudiant', 'Code etape', 'Annee', 'Montant paye',
                 'Date du dernier encaissement', 'Paiement partiel']]
        for i, ins in enumerate(bordereaux):
            total += int(ins.montant_paye)
            data.append([i+1, ins.num_commande, ins.nom, ins.prenom, ins.cod_etu, ins.cod_etp, ins.annee,
                         ins.montant_paye, ins.date_encaissement.strftime('%d/%m/%Y'), ins.is_partiel])
        data.append([total])
        filename = '/vagrant/bordereau_{}.xls'.format(bordereau_number)
        save_worksheet(filename, data)
    else:
        print 'Bordereau {} not found'.format(bordereau_number)


def print_statistics():
    inscriptions = PaiementParInscription.objects.select_related('wish').filter(wish__isnull=False)
    paiement_cb = 0
    paiement_v = 0

    droit_cb = 0
    frais_cb = 0
    droit_v = 0
    frais_v = 0
    for ins in inscriptions:
        if ins.paiment_type == 'CB':
            paiement_cb += 1
            droit_cb += ins.wish.droit_total()
            frais_cb += ins.wish.frais_peda()
            # if ins.bordereau ==
        elif ins.paiment_type == 'V':
            paiement_v += 1
            droit_v += ins.wish.droit_total()
            frais_v += ins.wish.frais_peda()

    print 'CB: {} V: {}'.format(paiement_cb, paiement_v)
    print 'CB Droit {} Frais {}'.format(droit_cb, frais_cb)
    print 'Virement Droit {} Frais {}'.format(droit_v, frais_v)


class Command(BaseCommand):
    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('--print',
                            nargs='+',
                            type=int,
                            dest='print',
                            help='Print the bordereau(x) given as argument(s)')

        # Named (optional) arguments
        parser.add_argument('--create',
            action='store_true',
            dest='create',
            default=False,
            help='Create new bordereau')

    def handle(self, *args, **options):

        if options['print']:
            for bordereau in options['print']:
                imprimer_bordereau(bordereau)

        if options['create']:
            print 'Create borderau'
            create_bordereau()

        # print_statistics()
