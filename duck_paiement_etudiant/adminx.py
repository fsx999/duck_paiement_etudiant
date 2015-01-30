from django.views.decorators.cache import never_cache
from django_apogee.models import InsAdmEtp
from duck_paiement_etudiant.models import AnneeUniPaiement

__author__ = 'paulguichon'
from xadmin import views
import xadmin


class GestionFinnacierAnnee(views.Dashboard):
    base_template = 'duck_paiement_etudiant/gestion_financiere_annee.html'
    widget_customiz = False

    def get_context(self):
        context = super(GestionFinnacierAnnee, self).get_context()
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
xadmin.site.register_view(r'^gestion_financiere/$', GestionFinnacierAnnee, 'gestion_financiere_annee')


class PaiementAdminView(object):
    pass
    # def get_urls(self, ):

xadmin.site.register(InsAdmEtp, PaiementAdminView)
print xadmin.site.get_urls()