__author__ = 'paulguichon'
from xadmin import views
import xadmin

class GestionFinnacierAnnee(views.Dashboard):
    base_template = 'duck_paiement_etudiant/gestion_financiere_annee.html'
    widget_customiz = False

    # def get_context(self):
    #     context = super(StatistiquePal, self).get_context()
    #     context['etapes'] = SettingsEtape.objects.filter(is_inscription_ouverte=True).order_by('diplome')
    #     return context
    #
    # @filter_hook
    # def get_breadcrumb(self):
    #     return [{'url': self.get_admin_url('index'), 'title': 'Accueil'},
    #             {'url': self.get_admin_url('statistiques'), 'title': 'Statistique'},
    #             {'url': self.get_admin_url('stats_pal'), 'title': 'Statistique PAL'}]
    #
    # @never_cache
    # def get(self, request, *args, **kwargs):
    #     self.widgets = self.get_widgets()
    #     return self.template_response(self.base_template, self.get_context())
xadmin.site.register_view(r'^gestion_financiere/$', GestionFinnacierAnnee, 'gestion_financiere_annee')