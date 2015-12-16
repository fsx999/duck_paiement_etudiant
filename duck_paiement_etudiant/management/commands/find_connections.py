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
                        break
                        # Ask me which I want to choose
                        print 'https://backoffice.iedparis8.net/django_apogee/individu/{}/update/'\
                            .format(ins.cod_ind__cod_ind)
                        for i, ind in enumerate(ind_found):
                            print '{}. https://backoffice.iedparis8.net/duck_inscription/individu/{}/update/'.format(i+1, ind.id)
                        choice = give_options(1, len(ind_found)) - 1

                    # Individu.objects.get(code_opi=individus[0].code_opi)
                    defaults = {'individu': ind_found[choice]}
                    PaiementParInscription.objects.update_or_create(
                        cod_etp=ins.cod_etp, cod_anu=2015, cod_vrs_vet=ins.cod_vrs_vet, num_occ_iae=ins.num_occ_iae,
                        cod_ind=ins.cod_ind__cod_ind, defaults=defaults
                    )
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
                            defaults = {'individu': ind_found[0]}
                            PaiementParInscription.objects.update_or_create(
                                cod_etp=ins.cod_etp, cod_anu=2015, cod_vrs_vet=ins.cod_vrs_vet, num_occ_iae=ins.num_occ_iae,
                                cod_ind=ins.cod_ind__cod_ind, defaults=defaults
                            )
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

            defaults = {'wish': wishes[choice]}
            PaiementParInscription.objects.update_or_create(
                cod_etp=ins.cod_etp, cod_anu=2015, cod_vrs_vet=ins.cod_vrs_vet, num_occ_iae=ins.num_occ_iae,
                cod_ind=ins.cod_ind, defaults=defaults
            )




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


def add_missing_ins(etu_to_etudiant):
    '''
    Adds missing inscriptions to the table PaiementParInscription
    :return:
    '''

    for cod_etu, etu in etu_to_etudiant.items():
        for ins in etu.inscriptions:
            defaults = {'cod_etu': cod_etu}
            inscription = PaiementParInscription.objects.update_or_create(
                cod_etp=ins.cod_etp, cod_anu=2015, cod_vrs_vet=ins.cod_vrs_vet, num_occ_iae=ins.num_occ_iae,
                cod_ind=ins.cod_ind__cod_ind, defaults=defaults
            )

    return etu_to_etudiant


class Command(BaseCommand):

    def handle(self, *args, **options):
        tested_by_hand = {
            '15609653': 7721112, #MEZIOUT BRAHIMI MALIKA, nom prenom inversees
            '14511097': 7718634, #PEDRONO ANNE-CLAIRE, same ine by mistake
            '11299481': 7722497, #PAPAGEORGIOU STYLIANI MARIA, wrong name, and surname by mistake
        }

        opi_wrong_birthday = ['15608970', '11296888', '12320445', '15609868', '10277022', '12320380']

        individus = Individu.objects.all().filter(wishes__isnull=False).prefetch_related(
            'wishes__paiementallmodel',
            'wishes__paiementallmodel__moyen_paiement',
            'wishes__paiementallmodel__paiement_request',
            'wishes__etape'
        ).distinct()

        inscriptions = get_inscriptions(True, 'etudiants.pickle')
        etu_to_etudiant = get_etudiants(inscriptions)
        # add_missing_ins(etu_to_etudiant)
        ins_paiement = PaiementParInscription.objects.filter(wish__isnull=True)

        etu_double_cursus = sum(len(x.inscriptions) > 1 for x in etu_to_etudiant.values())

        print 'Individus: {}'.format(individus.count())
        print 'Inscriptions: {}'.format(ins_paiement.count())
        print 'Double cursus: {}'.format(etu_double_cursus)

        no_ind = ins_paiement.filter(individu__isnull=True).values('cod_etu')

        # for cod_etu, etu in etu_to_etudiant.items():
        #     if len(etu.inscriptions) > 1:
        #         ins_list = [ins.cod_etp for ins in etu.inscriptions]
                # print '{} {}'.format(cod_etu, ins_list)

        # o = individus_etu['12318389'].wishes.all()[0].etape
        # pprint(vars(o))
        # return

        find_correspondance_etu_to_ind(etu_to_etudiant, individus, no_ind, manual=tested_by_hand)

        etudiants_not_found = PaiementParInscription.objects.filter(individu__isnull=True).count()
        etudiants_found = PaiementParInscription.objects.filter(individu__isnull=False).count()

        # print nombre_not_found
        print 'Etudiants found {}'.format(etudiants_found)
        print 'Etudiants not found {}'.format(etudiants_not_found)

        # Correspond wishes to inscriptions
        wish_not_found = PaiementParInscription.objects.select_related('individu')\
            .filter(individu__isnull=False, wish__isnull=True)

        wish_found = PaiementParInscription.objects.filter(individu__isnull=False, wish__isnull=False)

        find_correspondance_to_wish(wish_not_found)

        wish_not_found = PaiementParInscription.objects.filter(individu__isnull=False, wish__isnull=True)

        print 'Wish found {}'.format(wish_found.count())
        print 'Wish not found {}'.format(wish_not_found.count())
        return None


        # Find payments by CB
        wish_cb = {}
        pickle_file = 'info_cb.pickle'
        if os.path.isfile(pickle_file):
            wish_cb = pickle.load(open(pickle_file, "rb"))

        added = 0
        for i, ind in enumerate(individus):
            for wish in ind.wishes.all():
                dossier = int(wish.code_dossier)
                if dossier not in wish_cb:
                    try:
                        # print '{}: {}'.format(i, ind)
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
                            print 'Save CB pickle'
                            pickle.dump(wish_cb, open(pickle_file, "wb"))

                    except PaiementAllModel.DoesNotExist:
                        continue
                    except DuckInscriptionPaymentRequest.DoesNotExist:
                        continue

        print 'Total wishes with cb selected: {}'.format(len(wish_cb))

        wish_payed_cb = {}
        for code_dossier, info_cb in wish_cb.items():
            if info_cb['commonResponse']['responseCode'] == 0:
                wish_payed_cb[code_dossier] = info_cb

        print 'Total wishes payed with cb: {}'.format(len(wish_payed_cb))

        etu_all_wishes_cb = 0
        etu_correct_wishes_cb = 0
        for cod_etu, etu in etu_to_etudiant.items():
            all_found = 0
            correct_found = 0
            for ind in etu.individus:
                for w in ind.wishes.all():
                    if int(w.code_dossier) in wish_payed_cb:
                        etu_all_wishes_cb += 1
                        all_found += 1
            for ins in etu.inscriptions:
                for w in ins.wishes:
                    if int(w.code_dossier) in wish_payed_cb:
                        etu_correct_wishes_cb += 1
                        correct_found += 1

            if all_found != correct_found:
                ins = etu.inscriptions[0]
                print '{}, {} {}'.format(cod_etu, ins.last_name, ins.first_name1)

        print 'Etudiants All Carte Bancaire: {}'.format(etu_all_wishes_cb)
        print 'Etudiants Correct Carte Bancaire: {}'.format(etu_correct_wishes_cb)

        for ins in etu_to_etudiant[11297879].inscriptions:
            for w in ins.wishes:
                if int(w.code_dossier) in wish_cb:
                    print wish_cb[int(w.code_dossier)]
        for ind in etu_to_etudiant[11297879].individus:
            for wish in ind.wishes.all():
                dossier = int(wish.code_dossier)
                # print '{}: {}'.format(i, ind)
                paiement = wish.paiementallmodel
                moyen = paiement.moyen_paiement
                if moyen and moyen.type == 'CB':
                    request = paiement.paiement_request
                    status = dict(request.status_paiement())
                    print status

        multiple_wishes = 0
        multiple_wishes_cb = 0
        too_many_wishes_cb = 0
        for cod_etu, etu in etu_to_etudiant.items():
            for ins in etu.inscriptions:
                if etu.individus and len(ins.wishes) > 1:
                    multiple_wishes += 1
                    wish_found = 0
                    for wish in ins.wishes:
                        if int(wish.code_dossier) in wish_payed_cb:
                            ins.the_wish = wish
                            wish_found += 1
                    if wish_found > 0:
                        multiple_wishes_cb += 1
                        if wish_found > 1:
                            ins.the_wish = None
                            print '{} {}'.format(cod_etu, etu.individus)
                            too_many_wishes_cb += 1
                elif ins.wishes:
                    ins.the_wish = ins.wishes[0]

        print 'Multiple wishes {}'.format(multiple_wishes)
        print 'Multiple wishes, one payed by CB {}'.format(multiple_wishes_cb)
        print 'Multiple wishes, many payed by CB {}'.format(too_many_wishes_cb)

        the_wish_found = 0
        amounts_found = 0
        positive_amounts_found = 0
        for cod_etu, etu in etu_to_etudiant.items():
            for ins in etu.inscriptions:
                if ins.the_wish:
                    the_wish_found += 1
                    code_dossier = int(ins.the_wish.code_dossier)
                    if code_dossier in wish_payed_cb:
                        amounts_found += 1
                        request = wish_payed_cb[code_dossier]
                        total_amount = 0
                        for i in request['transactionItem']:
                            if i['transactionStatusLabel'] == 'CAPTURED':
                                total_amount += int(i['amount'])
                            elif i['transactionStatusLabel'] in ['WAITING_AUTHORISATION', 'AUTHORISED']:
                                ins.waiting = True
                            elif i['transactionStatusLabel'] not in ['REFUSED', 'CANCELLED']:
                                print i['transactionStatusLabel']
                        ins.amount_payed = total_amount
                        if total_amount > 0:
                            positive_amounts_found += 1
                        # print total_amount

        print 'The wish found {}'.format(the_wish_found)
        print 'Amounts found {}'.format(amounts_found)
        print 'Positive amounts found {}'.format(amounts_found)

        is_equal = 0
        not_equal = 0
        waiting = 0
        for cod_etu, etu in etu_to_etudiant.items():
            for ins in etu.inscriptions:
                if ins.the_wish and ins.amount_payed > 0:
                    wish = ins.the_wish
                    # Have to consider only CAPTURED as payed
                    amount_payed = float(ins.amount_payed)/100.0
                    theoritical_total = wish.droit_total() + wish.frais_peda()
                    if not ins.waiting:
                        if (theoritical_total - amount_payed) >= 0.01:
                            # print '{} {}'.format((theoritical_total - amount_payed) <= 0.01, (theoritical_total - amount_payed))
                            not_equal += 1
                            print '{} Droit: {} Frais: {} ({}) Payed: {} ({})'\
                                .format(etu.individus[0].code_opi, wish.droit_total(), wish.frais_peda(),
                                        theoritical_total, amount_payed, ins.amount_payed)
                        else:
                            is_equal += 1
                    elif ins.waiting:
                        waiting += 1

        print 'Equal {}'.format(is_equal)
        print 'Waiting {}'.format(waiting)
        print 'Not equal {}'.format(not_equal)
        return

        weird_cases = 0
        for cod_etu in etu_to_ind:
            etudiant_payed = cod_etu in etudiants_cb
            wish_payed = cod_etu in wishes_cb
            if etudiant_payed != wish_payed:

                ins = etu_to_ins[int(cod_etu)][0]
                code_opi = etu_to_ind[cod_etu]['ind'].code_opi
                print '{} {}, {} {}'.format(cod_etu, code_opi, ins['cod_ind__lib_nom_pat_ind'], ins['cod_ind__lib_pr1_ind'])

                weird_cases += 1

        print 'Weird CB cases: {}'.format(weird_cases)



        # print InsAdmEtpInitial._meta.db_table
#         cursor = connections['oracle'].cursor()
#         inscriptions = cursor.execute("""
# SELECT "INS_ADM_ETP"."COD_ANU", "INS_ADM_ETP"."COD_IND" cod_ind,
#  "INS_ADM_ETP"."COD_ETP", "INS_ADM_ETP"."COD_VRS_VET", "INS_ADM_ETP"."NUM_OCC_IAE", "INS_ADM_ETP"."COD_DIP",
#   "INS_ADM_ETP"."COD_CGE", "INS_ADM_ETP"."DAT_CRE_IAE", "INS_ADM_ETP"."DAT_MOD_IAE", "INS_ADM_ETP"."NBR_INS_CYC",
#   "INS_ADM_ETP"."NBR_INS_ETP", "INS_ADM_ETP"."DAT_ANNUL_RES_IAE", "INS_ADM_ETP"."TEM_IAE_PRM", "INS_ADM_ETP"."NBR_INS_DIP",
#    "INS_ADM_ETP"."ETA_IAE", "INS_ADM_ETP"."ETA_PMT_IAE", "INS_ADM_ETP"."COD_PRU", "INS_ADM_ETP"."COD_VRS_VDI"
#     FROM "INS_ADM_ETP" WHERE cod_anu=2015 and cod_cge='IED'""")

        # for result in inscriptions:
        #     print result