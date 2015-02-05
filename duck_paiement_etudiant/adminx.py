# coding=utf-8
from django.forms import Media
from django.forms.models import inlineformset_factory
from django.views.decorators.cache import never_cache
from django_apogee.models import InsAdmEtp
from duck_paiement_etudiant.models import AnneeUniPaiement, PaiementBackoffice, Banque
from xadmin.views import filter_hook

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
    readonly_fields = ['num_paiement', 'bordereau']
    extra = 1
    max_num = 3

    # @property
    # def get_exclude(self):
    #     return self.exclude
    #
    # @filter_hook
    # def get_readonly_fields(self):
    #     return self.readonly_fields
    #
    # @filter_hook
    # def get_formset(self, **kwargs):
    #     """Returns a BaseInlineFormSet class for use in admin add/change views."""
    #     if self.get_exclude is None:
    #         exclude = []
    #     else:
    #         exclude = list(self.get_exclude)
    #     exclude.extend(self.get_readonly_fields())
    #     if self.get_exclude is None and hasattr(self.form, '_meta') and self.form._meta.exclude:
    #         # Take the custom ModelForm's Meta.exclude into account only if the
    #         # InlineModelAdmin doesn't define its own.
    #         exclude.extend(self.form._meta.exclude)
    #     # if exclude is an empty list we use None, since that's the actual
    #     # default
    #     exclude = exclude or None
    #     can_delete = self.can_delete and self.has_delete_permission()
    #     defaults = {"form": self.form, "formset": self.formset, "fk_name": self.fk_name, "exclude": exclude,
    #                 "formfield_callback": self.formfield_for_dbfield, "extra": self.extra, "max_num": self.max_num,
    #                 "can_delete": can_delete, }
    #     defaults.update(kwargs)
    #     return inlineformset_factory(self.parent_model, self.model, **defaults)


class PaiementAdminView(object):
    fields = ['cod_ind']
    readonly_fields = ['cod_ind']
    inlines = [PaiementInlineView]
    search_fields = ['cod_ind__cod_etu']
    hidden_menu = True
    show_bookmarks = False
    site_title = u'Dossiers financiers étudiants'

    def get_media(self, *args, **kwargs):
        media = super(PaiementAdminView, self).get_media(*args, **kwargs)
        m = Media()
        m.add_js(['paiement_etudiant/js/paiement_etudiant.js'])
        return media+m



class PaimentAdminAnneeList(views.ListAdminView):

    def queryset(self):

        queryset = super(PaimentAdminAnneeList, self).queryset()

        return queryset.filter(cod_anu=self.kwargs['year'])


xadmin.site.register_modelview(r'^annee/(?P<year>\w+)/$', PaimentAdminAnneeList, name='%s_%s_annee_list')

class BanqueAdmin(object):
    pass

xadmin.site.register(InsAdmEtp, PaiementAdminView)
xadmin.site.register(Banque, BanqueAdmin)