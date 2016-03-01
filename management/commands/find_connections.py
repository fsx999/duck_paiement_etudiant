import pickle
from difflib import SequenceMatcher
from datetime import datetime
from django.db import connections
from pprint import pprint
from duck_inscription_payzen.models import PaiementAllModel, DuckInscriptionPaymentRequest
from unidecode import unidecode
from duck_paiement_etudiant.models import PaiementParInscription
from duck_recruitment.models import SettingsEtapes
import os
from django.core.management.base import BaseCommand
from django.db.models import Count, Q, F
from duck_inscription.models import Individu, Wish
from django_apogee.models import InsAdmEtpInitial
# from duck_scripts.utils import flatten


def flatten(argument):
    '''
    Takes argument, transforms it to string, removes accents, transforms it to uppercase, and strips trailing spaces
    :param string: Argument to transform
    :return: Transformed string
    '''
    return unidecode(argument).upper().strip()


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
    Returns user inscriptions from apogee
    :param use_pickle: Boolean, weather or not to use the pickle file directly
    :param pickle_file: Filename of the picklefile
    :return: Student inscriptions from apogee, either by db query (use_pickle: False) or from the pickle file (use_pickle: True)
    '''

    if use_pickle and os.path.isfile(pickle_file):
        print "Use Pickle"
        etudiants = pickle.load(open(pickle_file, "rb"))
    else:
        etapes = [x[0] for x in SettingsEtapes.objects.values_list('cod_etp') if x[0] != u'AUDLIB']
        print 'List of etapes'
        print etapes
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
    '''
    Return a dictionary of students. Each student has a list of inscriptions (one per diplome).
    :param inscriptions: Inscriptions in apogee
    :return: Dictionary: [cod_etu] --> Etudiant instance
    '''
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


def is_same_person(i, e):
    '''
    Compares two persons
    :param i: Person 1
    :param e: Person 2
    :return: Boolean, True if the persons compared are the same
    '''
    i_nom = flatten(i.last_name)
    e_nom = flatten(e.last_name)
    i_prenom = flatten(i.first_name1)
    e_prenom = flatten(e.first_name1)
    if i.birthday == e.birthday:
        if i_nom == e_nom and i_prenom == e_prenom:
            return True
        else:
            # ratio = round(SequenceMatcher(None, i_nom + i_prenom, e_nom + e_prenom).ratio(), 2)
            # if ratio < 0.7:
            #     pass
            # print '{}, {}, {}, {}, {}, {}, {}'.format(ratio, etudiant['cod_etp'], etudiant['cod_ind__cod_etu'], i_nom, i_prenom, e_nom, e_prenom)
            return False
    else:
        print '{} {}, {}, '.format(i.code_opi, i.birthday, e.birthday) + \
              '{}, {}, {}, {}, {}, {}'.format(e.cod_etp, e.cod_etu, i_nom, i_prenom, e_nom, e_prenom)
        return False


def give_options(start, end):
    '''
    Ask user to choose a number between start and end
    :param start: The first number a user can choose
    :param end: The last number a user can choose
    :return: The number a user has chosen
    '''
    print 'Choose between {} and {}'.format(start, end)
    while True:
        choice = int(raw_input())
        if start <= choice <= end:
            return choice
        else:
            print 'Please give a number between {} and {}'.format(start, end)


def find_individus(ins, individus, ind_etu, ind_ine, ind_opi):
    '''
    Return a list of individus for a given inscription
    :param ins: Inscription for which we are searching the corresponding individus
    :param individus: Queryset of all individus
    :param ind_etu: Dictionary [cod_etu] --> [List of individus]
    :param ind_ine: Dictionary [code ine] --> [List of individus]
    :param ind_opi: Dictionary [code opi] --> Individu
    :return: List of individus that correspond to inscription
    '''
    ine = ins.get_ine()
    cod_opi = ins.cod_ind__cod_ind_opi
    cod_etu = ins.cod_etu
    e_nom = ins.cod_ind__lib_nom_pat_ind
    e_prenom = ins.cod_ind__lib_pr1_ind
    ind_found = []

    if ine and ine in ind_ine:
        ind_found = ind_ine[ine]
    elif cod_etu and cod_etu in ind_etu:
        ind_found = ind_etu[cod_etu]
    elif cod_etu and cod_opi in ind_opi:
        ind_found = [ind_opi[cod_opi]]
    else:
        e_date = datetime.strptime(str(ins.cod_ind__date_nai_ind), '%Y-%m-%d %H:%M:%S').date()
        i_found = individus.filter(Q(first_name1__icontains=e_prenom) | Q(last_name__icontains=e_nom))\
            .filter(birthday=e_date)
        if i_found.exists():
            ind_found = [ind_opi[i.code_opi] for i in i_found]
    return ind_found


def is_same_individu(ins, ind_found):
    '''
    Let's user choose if the individu in ind_found is the same with the inscription ins
    :param ins: Inscription for which we are searching the individu
    :param ind_found: List of individus found
    :return: Boolean, the choice of the user (True or False)
    '''
    if len(ind_found) != 1:
        return False

    print 'Are they the same? \n0. False 1. True'
    print 'https://backoffice.iedparis8.net/django_apogee/individu/{}/update/'.format(ins.cod_ind__cod_ind)
    print 'https://backoffice.iedparis8.net/duck_inscription/individu/{}/update/'.format(ind_found[0].id)
    choice = give_options(0, 1)
    return bool(choice)


def choose_individu(ins, ind_found):
    '''
    Let's user choose the individu that corresponds to a given inscription
    :param ins: Inscription for which we are searching the individu
    :param ind_found: List of individus found
    :return: The index of the list of the individu that corresponds to the inscription
    '''

    if len(ind_found) > 1:
        print 'https://backoffice.iedparis8.net/django_apogee/individu/{}/update/'.format(ins.cod_ind__cod_ind)
        for i, ind in enumerate(ind_found):
            print '{}. https://backoffice.iedparis8.net/duck_inscription/individu/{}/update/'.format(i+1, ind.id)
        choice = give_options(1, len(ind_found)) - 1
    else:
        choice = 0
    return choice


def find_correspondance_etu_to_ind(etu_to_etudiant, individus, no_ind):
    '''
    Each student corresponds to a list of individu
    Find which student corresponds at which individu.
    :param etu_to_etudiant: Dictionary of all students and their inscriptions. (Cod_etu) --> Etudiant
    :param individus: Queryset with all Individus
    :return:
    '''

    # Many individuals can have the same cod_etu or ine, but there is only one opi for each individual
    individus_etu = {}
    individus_ine = {}
    for ind in individus:
        individus_etu.setdefault(str(ind.student_code), []).append(ind)
        individus_ine.setdefault(str(ind.ine).upper(), []).append(ind)
    individus_opi = {ind.code_opi: ind for ind in individus}

    for cod_etu in no_ind:
        cod_etu = int(cod_etu['cod_etu'])
        if cod_etu in etu_to_etudiant:
            etu = etu_to_etudiant[cod_etu]
            for ins in etu.inscriptions:

                ind_found = find_individus(ins, individus, individus_etu, individus_ine, individus_opi)

                if len(ind_found) == 0:
                    break
                count_different_ind = sum([1 for ind in ind_found if not is_same_person(ind, ins)])
                if count_different_ind == 0 or len(ind_found) > 1:
                    # If multiple choices exist for the same person, ask me which I want to choose
                    choice = choose_individu(ins, ind_found)
                    update_paiment_par_ins(ins, {'individu': ind_found[choice]})
                    print 'Saved successfully'
                else:
                    # If the persons found are different between them
                    if is_same_individu(ins, ind_found):
                        update_paiment_par_ins(ins, {'individu': ind_found[0]})
                        print 'Saved successfully'

    etudiants_not_found = PaiementParInscription.objects.filter(individu__isnull=True).count()
    etudiants_found = PaiementParInscription.objects.filter(individu__isnull=False).count()
    print 'Etudiants found {}'.format(etudiants_found)
    print 'Etudiants not found {}'.format(etudiants_not_found)


def find_correspondance_to_wish(wish_not_found):
    '''
    Finds corresponding wish to PaiementParInscription that have individu but the wish is missing
    :param wish_not_found: Queryset of paiements that have individu, but don't have a wish
    :return:
    '''
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
            wish = wishes[choice]
            num_commande = None
            try:
                num_commande = wish.paiementallmodel.pk
            except:
                pass
            update_paiment_par_ins(ins, {'wish': wish, 'num_commande': num_commande})
            print 'Saved successfully'

    wish_found = PaiementParInscription.objects.filter(individu__isnull=False, wish__isnull=False)
    wish_not_found = PaiementParInscription.objects.filter(individu__isnull=False, wish__isnull=True)
    print 'Wish found {}'.format(wish_found.count())
    print 'Wish not found {}'.format(wish_not_found.count())

# def to_dict(obj):
#     '''
#     Converts payment request object to dictionary
#     :param obj: Payment request object
#     :return: Dictionary that contains the info we need from the payment request object
#     '''
#
#     nobj = {}
#
#     for key, value in obj.items():
#         # print '{} - {}'.format(key, value)
#         if key == 'requestId':
#             nobj[key] = str(value)
#         elif key == 'orderResponse':
#             nobj[key] = dict(value)
#             nobj[key]['extInfo'] = []
#             for v in nobj[key]['extInfo']:
#                 nobj[key]['extInfo'].append(dict(v))
#         elif type(value) == list:
#             nobj[key] = []
#             for v in value:
#                 nobj[key].append(dict(v))
#         else:
#             nobj[key] = dict(value)
#     return nobj


def add_missing_ins():
    '''
    Adds missing inscriptions to the table PaiementParInscription
    :return:
    '''
    inscriptions = get_inscriptions(False, 'etudiants.pickle')
    etu_to_etudiant = get_etudiants(inscriptions)
    for cod_etu, etu in etu_to_etudiant.items():
        nom = etu.inscriptions[0].last_name
        prenom = etu.inscriptions[0].first_name1
        for ins in etu.inscriptions:
            update_paiment_par_ins(ins, {'cod_etu': cod_etu, 'nom': nom, 'prenom': prenom, 'annee': 2015})

    etu_double_cursus = sum(len(x.inscriptions) > 1 for x in etu_to_etudiant.values())
    print 'Double cursus: {}'.format(etu_double_cursus)

    return etu_to_etudiant


def update_paiment_par_ins(ins, defaults):
    '''
    Update or create a given inscription
    :param ins: Inscription to update or create
    :param defaults: Values to update in inscription
    :return: Inscription updated or created
    '''
    try:
        inscription = PaiementParInscription.objects.update_or_create(
            cod_etp=ins.cod_etp, cod_anu=2015, cod_vrs_vet=ins.cod_vrs_vet, num_occ_iae=ins.num_occ_iae,
            cod_ind=ins.cod_ind, defaults=defaults
        )
        return inscription
    except:
        # Can fail if for example we enter a wish_id that already exists, as wishes should be unique
        print 'Failed to update paiement par ins'
        print vars(ins)


def download_payment(wish):
    '''
    Download all info for one payment, inclouding the info about reimbursements and installments
    if the payment was done in installments.
    :param wish: Instance of the Wish model
    :return: List of transactions in the payment
    '''

    request = wish.paiementallmodel.paiement_request
    status = request.status_paiement()

    if status['commonResponse']['responseCode'] != 0:
        if status['commonResponse']['responseCode'] != 10:
            # 10 is the code for transaction not found
            print 'Thats a very weird code: ' + status['commonResponse']['responseCode']
        return None

    payments = []
    for item in status['transactionItem']:
        uuid = item['transactionUuid']
        transaction = request.payment_details(uuid)
        keep_info = {
            'amount': transaction['paymentResponse']['amount'],
            'operationType': transaction['paymentResponse']['operationType'],
            'expectedCaptureDate': transaction['paymentResponse']['expectedCaptureDate'],
            'transactionStatusLabel': transaction['commonResponse']['transactionStatusLabel']
        }
        payments.append(keep_info)

        print 'Operation type: {}'.format(keep_info['operationType'])

    return payments


def download_transactions(individus, pickle_file):
    '''
    Downloads payment info for all individus and saves them in the pickle_file
    :param individus: Queryset of individus of which the payment info will be downloaded
    :param pickle_file: Filename to save the payment info downloaded
    :return: A dictionary with all the payment info, [wish code dossier] --> Dictionary of Payment info
    '''

    wish_cb = {}
    if os.path.isfile(pickle_file):
        wish_cb = pickle.load(open(pickle_file, "rb"))

    added = 0
    for i, ind in enumerate(individus):
        for wish in ind.wishes.all():
            print '{}'.format(i)
            dossier = int(wish.code_dossier)
            # TODO Reactivate this line
            if dossier not in wish_cb or dossier == 10026851:
            # if dossier == 10029519:
                try:
                    # print '{}: {}'.format(i, ind)
                    paiement = wish.paiementallmodel
                    moyen = paiement.moyen_paiement
                    if moyen and moyen.type == 'CB':
                        payment = download_payment(wish)
                        wish_cb[dossier] = payment

                        added += 1

                        print '{} {}'.format(added, i)
                        if added % 20 == 19:
                            print 'Save CB pickle'
                            pickle.dump(wish_cb, open(pickle_file, "wb"))

                except PaiementAllModel.DoesNotExist:
                    continue
                except DuckInscriptionPaymentRequest.DoesNotExist:
                    continue

    print 'Added: {}'.format(added)
    print 'Save CB pickle'
    pickle.dump(wish_cb, open(pickle_file, "wb"))

    print 'Total wishes with cb selected: {}'.format(len(wish_cb))

    wish_cb_exist = {}
    for key, value in wish_cb.items():
        if value:
            wish_cb_exist[key] = value
    print 'Total wishes payed with cb: {}'.format(len(wish_cb))
    return wish_cb_exist


# TODO Pass wish_cb to new version
def parse_amounts(transactions):
    '''
    Calculates total amount payed in a payment request
    :param transactions: The dictionary of a payment request
    :return: A tuple containing the total amount captured, and the total amount waiting authorisation to be payed
    '''
    total_amount_captured = 0
    total_amount_reimbursed = 0
    total_amount_waiting = 0
    last_date = None

    # if len(request['transactionItem']) > 3:
    #     pprint(dict(request))
    for i, transaction in enumerate(transactions):
        if transaction['transactionStatusLabel'] == 'CAPTURED':
            amount = float(transaction['amount'])/100.0
            if transaction['operationType'] == 0:
                total_amount_captured += amount
            else:
                total_amount_reimbursed += amount
        elif transaction['transactionStatusLabel'] in ['WAITING_AUTHORISATION', 'AUTHORISED']:
            # Is this calculation even correct? Commented is the original calculation which seemed wrong
            # total_amount_waiting += float(i['amount'])/100.0 - ins.wish.droit_total()
            total_amount_waiting += float(transaction['amount'])/100.0
        elif transaction['transactionStatusLabel'] not in ['REFUSED', 'CANCELLED']:
            print transaction['transactionStatusLabel']

        current_date = transaction['expectedCaptureDate']
        if i == 0 or current_date > last_date:
            last_date = current_date

    # print last_date

    return total_amount_captured, total_amount_waiting, total_amount_reimbursed, last_date


def is_equal_to_theory(wish, amount_payed):
    '''
    Compares the amount payed, to the amount the individual should pay in theory
    :param wish: Instance of the Wish model
    :param amount_payed: The amount payed by CB
    :return: True if the amount payed is equal to the amount that should be paied in theory. It allows for an error of
    1 centime.
    '''
    theoritical_total = wish.droit_total() + wish.frais_peda()
    return abs(theoritical_total - amount_payed) <= 0.01


# def is_reimbursed(wish, amount_payed):
#     '''
#     Returns true if the frais pedagogiques were reimbursed to the student
#     :param wish: Instance of the Wish model
#     :param amount_payed: The amount payed by CB (includes the amount reimbursed)
#     :return: True if the frais pedagogiques were reimbursed to the student
#     '''
#     theoritical_total = wish.droit_total() + 2 * wish.frais_peda()
#     theoritical_total_2 = 2 * wish.droit_total() + 2 * wish.frais_peda()
#     return (theoritical_total - amount_payed) <= 0.01 or (theoritical_total_2 - amount_payed) <= 0.02


def find_amount_payed(wish_payed_cb):
    '''
    Calculate the amount payed by each individual
    :param wish_payed_cb: Dictionary with the payment info for each wish
    :return:
    '''
    wish_found = PaiementParInscription.objects\
        .filter(individu__isnull=False, wish__isnull=False, bordereau__isnull=True)

    amounts_found = 0
    is_equal = 0
    not_equal = 0
    waiting = 0

    total_amount_with_error = 0
    total_amount_waiting = 0
    total_amount_reimbursed = 0
    total_amount_payed = 0

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

            amount_payed, amount_waiting, amount_reimbursed, last_date = parse_amounts(wish_payed_cb[code_dossier])
            is_waiting = True if amount_waiting > 0 else False

            if not is_waiting:
                if not is_equal_to_theory(ins.wish, amount_payed):
                    not_equal += 1
                    total_amount_with_error += amount_payed - ins.wish.droit_total()
                    print '{} Droit: {} Frais: {} ({}) Payed: {}'\
                        .format(ins.individu.code_opi, ins.wish.droit_total(), ins.wish.frais_peda(),
                                ins.wish.droit_total() + ins.wish.frais_peda(), amount_payed)
                    # I include the not equal to the borderaux, as partial payments
                    update_paiment_par_ins(ins, {'montant_paye': amount_payed - ins.wish.droit_total(),
                                                 'date_encaissement': last_date,
                                                 'is_partiel': True})
                else:
                    update_paiment_par_ins(ins, {'montant_paye': amount_payed - ins.wish.droit_total(),
                                                 'date_encaissement': last_date})
                    total_amount_payed += amount_payed - ins.wish.droit_total()
                    total_amount_reimbursed += amount_reimbursed
                    is_equal += 1
            elif is_waiting:
                total_amount_waiting += amount_waiting
                waiting += 1

            # print total_amount
    print 'Total amount payed {}, Total amount waiting {}, Total amount reimbursed {}, total amount with error {}'.\
        format(total_amount_payed, total_amount_waiting, total_amount_reimbursed, total_amount_with_error)

    print 'Amounts found {}'.format(amounts_found)
    print 'Equal {}'.format(is_equal)
    print 'Waiting {}'.format(waiting)
    print 'Not equal {}'.format(not_equal)


def update_bordereau_1(wish_payed_cb):
    wish_found = PaiementParInscription.objects.filter(bordereau=1)

    for ins in wish_found:
        code_dossier = int(ins.wish.code_dossier)
        amount_payed, amount_waiting, amount_reimbursed, last_date = parse_amounts(wish_payed_cb[code_dossier])

        update_paiment_par_ins(ins, {
            'date_encaissement': last_date,
            'droits': ins.wish.droit_total(),
            'frais': ins.wish.frais_peda(),
            'montant_recu': amount_payed,
            'montant_rembourse': amount_reimbursed
        })


def find_missing_transactions(wish_cb):
    '''
    Find transactions that are not in the PaiementParInscription table
    :param wish_cb: Dictionary with the payment info for each wish
    :return:
    '''
    wish_found = PaiementParInscription.objects.filter(individu__isnull=False, wish__isnull=False)
    dossier_to_paiement = {}
    for paiement in wish_found:
        dossier = paiement.wish.code_dossier
        dossier_to_paiement[dossier] = paiement

    errors = 0
    reimbursed = 0
    not_payed = 0
    other = 0

    for dossier, info_cb in wish_cb.items():
        if dossier not in dossier_to_paiement:
            amount_payed, amount_waiting, amount_reimbursed, last_date = parse_amounts(info_cb)
            if amount_payed > 0:
                wish = Wish.objects.get(code_dossier=dossier)
                # TODO Check if the remboursement was complete or partial
                if amount_reimbursed > 0:
                    reimbursed += 1
                elif str(wish.suivi_dossier) in ['inscription_refuse', 'inscription_annule', 'inscription_incomplet',
                                               'inscription_incom_r', 'inactif']:
                    errors += 1
                else:
                    # print wish.droit_total() + wish.frais_peda()
                    # print amount_payed
                    print wish.pk
                    print wish
                    print wish.suivi_dossier
                    other += 1
            else:
                not_payed += 1

    print 'Not payed {}, Reimbursed {}, Errors {}, Other: {}'.format(not_payed, reimbursed, errors, other)


def paied_too_much(wish, amount_payed):
    '''
    Return true if the person has payed more than the theoritical amount
    :param wish: Instance of the Wish model
    :param amount_payed: The amount payed by CB
    :return:
    '''
    theoritical_total = wish.droit_total() + wish.frais_peda()
    return amount_payed > theoritical_total


def find_abnormal_paiements(wish_payed_cb):
    paiements = PaiementParInscription.objects.filter(montant_paye__isnull=False)
    partial = PaiementParInscription.objects.filter(montant_paye__isnull=False, is_partiel=True).count()
    print 'Total number of amounts found {}'.format(paiements.count())
    too_much = 0
    equal = 0
    is_too_much = False
    changed = 0
    for paiement in paiements:
        wish = paiement.wish
        paye = paiement.montant_paye
        if paied_too_much(wish, paye + wish.droit_total()):
            too_much += 1
            is_too_much = True
            print 'Code dossier: {}'.format(wish.code_dossier)
            # if wish.code_dossier == 10032481:
            #     pprint(dict(wish_payed_cb[wish.code_dossier]))
            # pprint(vars(paiement))
        if is_equal_to_theory(wish, paye + wish.droit_total()):
            equal += 1
            if is_too_much:
                print 'WTF?????????????'
        # TODO Remove this line
        if int(wish.code_dossier) != 10029519:
            return
        else:
            print 'Here we are'
        paye_now = parse_amounts(wish_payed_cb[wish.code_dossier])[0] - wish.droit_total()
        if abs(paye_now - paye) > 0.1:
            # pprint(vars(paiement))
            # print 'Now: {}, Past: {}'.format(paye_now, paye)
            changed += 1

        is_too_much = False

    print 'Too much: {}, Equal: {}, Partial (Too little): {}'.format(too_much, equal, partial)
    print 'Total: {}'.format(too_much+equal+partial)
    print 'Changed over time: {}'.format(changed)


class Command(BaseCommand):

    def handle(self, *args, **options):

        individus = Individu.objects.all().filter(wishes__isnull=False).prefetch_related(
            'wishes__paiementallmodel',
            'wishes__paiementallmodel__moyen_paiement',
            'wishes__paiementallmodel__paiement_request',
            'wishes__etape'
        ).distinct()
        print 'Individus: {}'.format(individus.count())

        print 'Step 1'  # STEP 1: Add inscriptions that are missing from the PaiementParInscription table
        # etu_to_etudiant = add_missing_ins()
        ins_paiement = PaiementParInscription.objects.filter(wish__isnull=True)
        print 'Nouveaux Inscriptions: {}'.format(ins_paiement.count())
        no_ind = ins_paiement.filter(individu__isnull=True).values('cod_etu')

        print 'Step 2'  # STEP 2: Find correspondance between an inscription and an individu
        # find_correspondance_etu_to_ind(etu_to_etudiant, individus, no_ind)

        print 'Step 3'  # STEP 3: Find correspondance between an inscription and a particular wish of the individu
        wish_not_found = PaiementParInscription.objects.select_related('individu')\
            .filter(individu__isnull=False, wish__isnull=True, bordereau__isnull=True)
        # find_correspondance_to_wish(wish_not_found)

        print 'Step 4'  # STEP 4: Download all payment info and save them in a pickle
        wish_cb = download_transactions(individus, 'info_cb3.pickle')

        print 'Step 5'  # STEP 5: Associate students with the amount they payed by CB
        # find_amount_payed(wish_payed_cb)

        print 'Step 6'  # STEP 6: Find transactions that are not in the PaiementParInscription table
        # find_missing_transactions(wish_cb)

        print 'Step 7'
        # find_abnormal_paiements(wish_cb)

        # info_1 = wish_payed_cb.values()[0]
        # pprint(dict(info_1))
        # pprint(vars(o))

        update_bordereau_1(wish_cb)
