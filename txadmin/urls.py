from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^$', 'tickets.txadmin.views.index'),
    (r'^occurrence/(?P<occurrence_id>\d+)/purchases/$',
        'tickets.txadmin.views.occurrence_purchases'),
    (r'^occurrence/(?P<occurrence_id>\d+)/stats/$',
        'tickets.txadmin.views.occurrence_stats'),
    (r'^purchase/(?P<purchase_id>\d+)/delete/$',
        'tickets.txadmin.views.purchase_delete'),
)
