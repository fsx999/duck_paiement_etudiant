import pickle
from difflib import SequenceMatcher
from datetime import datetime
from django.db import connections
from pprint import pprint
from duck_inscription_payzen.models import PaiementAllModel, DuckInscriptionPaymentRequest
from duck_paiement_etudiant.models import PaiementParInscription
from duck_recruitment.models import SettingsEtapes
import os
from django.core.management.base import BaseCommand
from django.db.models import Count, Q, F
from duck_inscription.models import Individu, Wish
from django_apogee.models import InsAdmEtpInitial
from django_apogee.utils import flatten


class Inscription:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.last_name = kwargs['cod_ind__lib_nom_pat_ind']
        self.first_name1 = kwargs['cod_ind__lib_pr1_ind']
        self.birthday = datetime.strptime(str(kwargs['cod_ind__date_nai_ind']), '%Y-%m-%d %H:%M:%S').date()
        self.cod_etu = kwargs['cod_ind__cod_etu']
        self.cod_ind = kwargs['cod_ind__cod_ind']
        self.wishes = []
        self.the_wish = None
        self.amount_payed = 0
        self.waiting = False

    def get_ine(self):
        ine = self.cod_ind__cod_nne_ind + self.cod_ind__cod_cle_nne_ind
        return str(ine).upper()

    def append_wish(self, wish):
        '''
        Appends wish to wishes, if it is for same or similar cod_etp to the current inscription
        '''
        if str(wish.etape.cod_etp)[2:] == str(self.cod_etp)[2:]:
            self.wishes.append(wish)

    def wishes_is_same(self):
        return [(w, str(w.etape.cod_etp) == str(self.cod_etp)) for w in self.wishes]


class Etudiant:
    def __init__(self, inscriptions):
        self.inscriptions = []
        for ins in inscriptions:
            self.inscriptions.append(Inscription(**ins))
        self.individus = []
        self.type = None

    def set_individus(self, ind_type, individus):
        self.type = ind_type
        self.individus = individus


def get_inscriptions(use_pickle, pickle_file):
    '''
    If use_pickle is False, executes the query to get student inscriptions from apogee, and pickles the result in picklefile
    If use_pickle is True, it will not execute the query and will use the pickle directly
    '''

    if use_pickle and os.path.isfile(pickle_file):
        print "Use Pickle"
        etudiants = pickle.load(open(pickle_file, "rb"))
    else:
        etapes = [x[0] for x in SettingsEtapes.objects.values_list('cod_etp')]
        etudiants = InsAdmEtpInitial.objects.using('oracle')\
            .select_related('cod_ind')\
            .filter(cod_etp__in=etapes, cod_anu='2015', eta_iae='E')\
            .values(
                'cod_etp',
                'cod_ind__cod_ind',
                'cod_vrs_vet',
                'num_occ_iae',
                'cod_ind__cod_etu', 'cod_ind__cod_nne_ind', 'cod_ind__cod_cle_nne_ind',
                'cod_ind__lib_nom_pat_ind', 'cod_ind__lib_nom_usu_ind',
                'cod_ind__lib_pr1_ind', 'cod_ind__lib_pr2_ind', 'cod_ind__lib_pr3_ind',
                'cod_ind__num_brs_etu', 'cod_ind__cod_nni_etu', 'cod_ind__cod_cle_nni_etu',
                'cod_ind__cod_sex_etu', 'cod_ind__date_nai_ind',
                'cod_ind__cod_ind_opi',
            )
        print "Create Pickle"
        pickle.dump(etudiants, open(pickle_file, "wb"))
    return etudiants


def get_etudiants(inscriptions):
    etu_ins = {}
    for i in inscriptions:
        cod_etu = i['cod_ind__cod_etu']
        inscription = (i, i['cod_etp'])
        etu_ins.setdefault(cod_etu, []).append(inscription)

    etu_multi_ins = sum(len(x) > 1 for x in etu_ins.values())
    print 'Etudiants multi inscrits (AJAC ou double cursus): {}'.format(etu_multi_ins)

    etu_primary_ins = {}
    for cod_etu, l in etu_ins.items():
        l.sort(reverse=True)
        inscriptions = [x[0] for i, x in enumerate(l) if i == 0 or l[i][1][2:] != l[i-1][1][2:]]
        etu_primary_ins[cod_etu] = Etudiant(inscriptions)

    return etu_primary_ins


def is_same(string1, string2):
    return flatten(string1) == flatten(string2)


def is_same_person(i, e):
    i_nom = flatten(i.last_name)
    e_nom = flatten(e.last_name)
    i_prenom = flatten(i.first_name1)
    e_prenom = flatten(e.first_name1)
    if i.birthday == e.birthday:
        if i_nom == e_nom and i_prenom == e_prenom:
            return True
        else:
            ratio = round(SequenceMatcher(None, i_nom + i_prenom, e_nom + e_prenom).ratio(), 2)
            if ratio < 0.7:
                pass
            # print '{}, {}, {}, {}, {}, {}, {}'.format(ratio, etudiant['cod_etp'], etudiant['cod_ind__cod_etu'], i_nom, i_prenom, e_nom, e_prenom)
            return False
    else:
        print '{} {}, {}, '.format(i.code_opi, i.birthday, e.birthday) + \
              '{}, {}, {}, {}, {}, {}'.format(e.cod_etp, e.cod_etu, i_nom, i_prenom, e_nom, e_prenom)
        return False


def give_options(start, end):
    print 'Choose between {} and {}'.format(start, end)
    while True:
        choice = int(raw_input())
        if start <= choice <= end:
            return choice
        else:
            print 'Please give a number between {} and {}'.format(start, end)

def find_correspondance_etu_to_ind(etu_to_etudiant, individus, no_ind, **kwargs):
    '''
    Each student corresponds to a list of individu
    Find which student corresponds at which individu.
    :param etu_to_etudiant: Dictionary of all students and their inscriptions. (Cod_etu) --> [List of Etudiants]
    :param individus: Queryset with all Individus
    :param kwargs:
    :return:
    '''

    tested_by_hand = {}
    if 'manual' in kwargs:
        tested_by_hand = kwargs['manual']

    # Many individuals can have the same cod_etu or ine, but there is only one opi for each individual
    individus_etu = {}
    individus_ine = {}
    for ind in individus:
        individus_etu.setdefault(str(ind.student_code), []).append(ind)
        individus_ine.setdefault(str(ind.ine).upper(), []).append(ind)
    individus_opi = {ind.code_opi: ind for ind in individus}

    etu_to_ind = {}
    etudiants_not_found = {}

    for cod_etu in no_ind:
        cod_etu = int(cod_etu['cod_etu'])
        if cod_etu in etu_to_etudiant:
            etu = etu_to_etudiant[cod_etu]
            for ins in etu.inscriptions:
                ine = ins.get_ine()
                cod_opi = ins.cod_ind__cod_ind_opi
                e_nom = ins.cod_ind__lib_nom_pat_ind
                e_prenom = ins.cod_ind__lib_pr1_ind
                ind_found = []

                if cod_etu in tested_by_hand:
                    ind_found = [individus_opi[tested_by_hand[cod_etu]]]
                elif ine and ine in individus_ine:
                    ind_found =  individus_ine[ine]
                elif cod_etu and cod_etu in individus_etu:
                    ind_found = individus_etu[cod_etu]
                elif cod_etu and cod_opi in individus_opi:
                    ind_found = [individus_opi[cod_opi]]
                else:
                    e_date = datetime.strptime(str(ins.cod_ind__date_nai_ind), '%Y-%m-%d %H:%M:%S').date()
                    i_found = individus.filter(Q(first_name1__icontains=e_prenom) | Q(last_name__icontains=e_nom))\
                        .filter(birthday=e_date)
                    if i_found.exists():
                        found_list = [individus_opi[i.code_opi] for i in i_found]
                        ind_found = found_list
                    else:
                        etudiants_not_found[cod_etu] = ins

                if len(ind_found) == 0:
                    break
                count_different_ind = sum([1 for ind in ind_found if not is_same_person(ind, ins)])
                if count_different_ind == 0:
                    choice = 0
                    if len(ind_found) > 1:
                        # Ask me which I want to choose
                        print 'https://backoffice.iedparis8.net/django_apogee/individu/{}/update/'\
                            .format(ins.cod_ind__cod_ind)
                        for i, ind in enumerate(ind_found):
                            print '{}. https://backoffice.iedparis8.net/duck_inscription/individu/{}/update/'.format(i+1, ind.id)
                        choice = give_options(1, len(ind_found)) - 1

                    # Individu.objects.get(code_opi=individus[0].code_opi)
                    update_paiment_par_ins(ins, {'individu': ind_found[choice]})
                    print 'Saved successfully'

                else:
                    if len(ind_found) == 1:
                        break
                        # Ask me if I wish to change the name, surname, date de naissance
                        print 'Are they the same? \n0. False 1. True'
                        print 'https://backoffice.iedparis8.net/django_apogee/individu/{}/update/'\
                            .format(ins.cod_ind__cod_ind)
                        print 'https://backoffice.iedparis8.net/duck_inscription/individu/{}/update/'.format(ind_found[0].id)
                        choice = give_options(0, len(ind_found))

                        if choice == 1:
                            update_paiment_par_ins(ins, {'individu': ind_found[0]})
                            print 'Saved successfully'


def find_correspondance_to_wish(wish_not_found):
    for ins in wish_not_found:
        ind = ins.individu
        wishes = []
        for wish in ind.wishes.all():
            if str(wish.etape.cod_etp)[2:] == str(ins.cod_etp)[2:]:
                wishes.append(wish)

        if wishes:
            choice = 0
            if len(wishes) > 1:
                print 'https://backoffice.iedparis8.net/django_apogee/individu/{}/update/'.format(ins.cod_ind)
                print 'https://backoffice.iedparis8.net/duck_inscription/individu/{}/update/'.format(ind.id)
                for i, wish in enumerate(wishes):
                    print '{}. {}'.format(i+1, wish)
                choice = give_options(1, len(wishes)) - 1
                print 'Saved successfully'

            update_paiment_par_ins(ins, {'wish': wishes[choice]})


def to_dict(obj):
    nobj = {}

    for key, value in obj.items():
        # print '{} - {}'.format(key, value)
        if key == 'requestId':
            nobj[key] = str(value)
        elif key == 'orderResponse':
            nobj[key] = dict(value)
            nobj[key]['extInfo'] = []
            for v in nobj[key]['extInfo']:
                nobj[key]['extInfo'].append(dict(v))
        elif type(value) == list:
            nobj[key] = []
            for v in value:
                nobj[key].append(dict(v))
        else:
            nobj[key] = dict(value)
    return nobj


def add_missing_ins():
    '''
    Adds missing inscriptions to the table PaiementParInscription
    :return:
    '''
    inscriptions = get_inscriptions(True, 'etudiants.pickle')
    etu_to_etudiant = get_etudiants(inscriptions)
    for cod_etu, etu in etu_to_etudiant.items():
        for ins in etu.inscriptions:
            update_paiment_par_ins(ins, {'cod_etu': cod_etu})

    etu_double_cursus = sum(len(x.inscriptions) > 1 for x in etu_to_etudiant.values())
    print 'Double cursus: {}'.format(etu_double_cursus)

    return etu_to_etudiant


def update_paiment_par_ins(ins, defaults):
    inscription = PaiementParInscription.objects.update_or_create(
        cod_etp=ins.cod_etp, cod_anu=2015, cod_vrs_vet=ins.cod_vrs_vet, num_occ_iae=ins.num_occ_iae,
        cod_ind=ins.cod_ind, defaults=defaults
    )
    return inscription


def download_payment_info(individus, pickle_file):
    wish_cb = {}
    if os.path.isfile(pickle_file):
        wish_cb = pickle.load(open(pickle_file, "rb"))

    added = 0
    for ind in individus:
        for wish in ind.wishes.all():
            dossier = int(wish.code_dossier)
            if dossier not in wish_cb:
                try:
                    print '{}: {}'.format(i, ind)
                    paiement = wish.paiementallmodel
                    moyen = paiement.moyen_paiement
                    if moyen and moyen.type == 'CB':
                        request = paiement.paiement_request
                        status = dict(request.status_paiement())
                        # print status
                        wish_cb[dossier] = to_dict(status)
                        # print type(status)
                        # print to_dict(status)

                        added += 1

                        # print 'Save CB pickle'
                        # pickle.dump(wish_cb, open(pickle_file, "wb"))

                except PaiementAllModel.DoesNotExist:
                    continue
                except DuckInscriptionPaymentRequest.DoesNotExist:
                    continue

    print 'Save CB pickle'
    pickle.dump(wish_cb, open(pickle_file, "wb"))
    return wish_cb


class Command(BaseCommand):

    def handle(self, *args, **options):

        individus = Individu.objects.all().filter(wishes__isnull=False).prefetch_related(
            'wishes__paiementallmodel',
            'wishes__paiementallmodel__moyen_paiement',
            'wishes__paiementallmodel__paiement_request',
            'wishes__etape'
        ).distinct()

        # STEP 1: Add inscriptions that are missing from the PaiementParInscription table
        # etu_to_etudiant = add_missing_ins()
        ins_paiement = PaiementParInscription.objects.filter(wish__isnull=True)

        print 'Individus: {}'.format(individus.count())
        print 'Inscriptions: {}'.format(ins_paiement.count())

        no_ind = ins_paiement.filter(individu__isnull=True).values('cod_etu')

        # STEP 2: Find correspondance between an inscription and an individu
        # find_correspondance_etu_to_ind(etu_to_etudiant, individus, no_ind)

        etudiants_not_found = PaiementParInscription.objects.filter(individu__isnull=True).count()
        etudiants_found = PaiementParInscription.objects.filter(individu__isnull=False).count()
        print 'Etudiants found {}'.format(etudiants_found)
        print 'Etudiants not found {}'.format(etudiants_not_found)

        # STEP 3: Find correspondance between an inscription and a particular wish of the individu
        wish_not_found = PaiementParInscription.objects.select_related('individu')\
            .filter(individu__isnull=False, wish__isnull=True)

        find_correspondance_to_wish(wish_not_found)

        wish_found = PaiementParInscription.objects.filter(individu__isnull=False, wish__isnull=False)
        wish_not_found = PaiementParInscription.objects.filter(individu__isnull=False, wish__isnull=True)
        print 'Wish found {}'.format(wish_found.count())
        print 'Wish not found {}'.format(wish_not_found.count())

        # STEP 4: Download all payment info and save them in a pickle
        wish_cb = download_payment_info(individus, 'info_cb.pickle')

        wish_payed_cb = {}
        for code_dossier, info_cb in wish_cb.items():
            if info_cb['commonResponse']['responseCode'] == 0:
                wish_payed_cb[code_dossier] = info_cb

        print 'Total wishes with cb: {}'.format(len(wish_cb))
        print 'Total wishes payed with cb: {}'.format(len(wish_payed_cb))

        # STEP 5: Associate students with the amount they payed by CB

        wish_found = PaiementParInscription.objects.filter(individu__isnull=False, wish__isnull=False)

        amounts_found = 0
        is_equal = 0
        not_equal = 0
        waiting = 0

        for ins in wish_found:
            try:
                moyen = ins.wish.paiementallmodel.moyen_paiement
                if moyen:
                    update_paiment_par_ins(ins, {'paiment_type': moyen.type})
            except PaiementAllModel.DoesNotExist, DuckInscriptionPaymentRequest.DoesNotExist:
                pass

            code_dossier = int(ins.wish.code_dossier)
            if code_dossier in wish_payed_cb:
                amounts_found += 1
                request = wish_payed_cb[code_dossier]
                total_amount = 0
                is_waiting = False
                for i in request['transactionItem']:
                    if i['transactionStatusLabel'] == 'CAPTURED':
                        total_amount += int(i['amount'])
                    elif i['transactionStatusLabel'] in ['WAITING_AUTHORISATION', 'AUTHORISED']:
                        is_waiting = True
                    elif i['transactionStatusLabel'] not in ['REFUSED', 'CANCELLED']:
                        print i['transactionStatusLabel']
                amount_payed = float(total_amount)/100.0
                theoritical_total = ins.wish.droit_total() + ins.wish.frais_peda()
                if not is_waiting:
                    if (theoritical_total - amount_payed) >= 0.01:
                        # print '{} {}'.format((theoritical_total - amount_payed) <= 0.01, (theoritical_total - amount_payed))
                        not_equal += 1
                        print '{} Droit: {} Frais: {} ({}) Payed: {}'\
                            .format(ins.individu.code_opi, ins.wish.droit_total(), ins.wish.frais_peda(),
                                    theoritical_total, amount_payed)
                    else:
                        is_equal += 1
                elif is_waiting:
                    waiting += 1

                # print total_amount

        print 'Amounts found {}'.format(amounts_found)
        print 'Equal {}'.format(is_equal)
        print 'Waiting {}'.format(waiting)
        print 'Not equal {}'.format(not_equal)

        # pprint(vars(o))
