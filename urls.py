from django.conf.urls import patterns, url
from duck_paiement_etudiant.adminx import BordereauSpreadsheetView

urlpatterns = patterns(
    '',
    url(r'^impression_pdf/(?P<bordereau>\w+)$',
        BordereauSpreadsheetView.as_view(),
        name='bordereau_spreadsheet_pdf'),
    )

