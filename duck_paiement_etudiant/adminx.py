from django.views.decorators.cache import never_cache
from django_apogee.models import InsAdmEtp
from duck_paiement_etudiant.models import AnneeUniPaiement, PaiementBackoffice

__author__ = 'paulguichon'
from xadmin import views
import xadmin


class GestionFinanciereAnnee(views.Dashboard):
    base_template = 'duck_paiement_etudiant/gestion_financiere_annee.html'
    widget_customiz = False

    def get_context(self):
        context = super(GestionFinanciereAnnee, self).get_context()
        context['years'] = AnneeUniPaiement.objects.all().order_by('-cod_anu')
        return context
    #
    # @filter_hook
    # def get_breadcrumb(self):
    #     return [{'url': self.get_admin_url('index'), 'title': 'Accueil'},
    #             {'url': self.get_admin_url('statistiques'), 'title': 'Statistique'},
    #             {'url': self.get_admin_url('stats_pal'), 'title': 'Statistique PAL'}]
    #

    @never_cache
    def get(self, request, *args, **kwargs):
        self.widgets = self.get_widgets()
        return self.template_response(self.base_template, self.get_context())
xadmin.site.register_view(r'^gestion_financiere/$', GestionFinanciereAnnee, 'gestion_financiere_annee')


class PaiementInlineView(object):
    model = PaiementBackoffice
    exclude = ['cod_anu', 'cod_ind', 'cod_etp', 'cod_vrs_vet', 'num_occ_iae']
    readonly_fields = ['bordereau']
    extra = 1
    max_num = 3


class PaiementAdminView(object):
    fields = ['cod_ind']
    readonly_fields = ['cod_ind']
    inlines = [PaiementInlineView]




class PaimentAdminAnneeList(views.ListAdminView):

    def queryset(self):

        queryset = super(PaimentAdminAnneeList, self).queryset()

        return queryset.filter(cod_anu=self.kwargs['year'])


xadmin.site.register_modelview(r'^annee/(?P<year>\w+)/$', PaimentAdminAnneeList, name='%s_%s_annee_list')

xadmin.site.register(InsAdmEtp, PaiementAdminView)