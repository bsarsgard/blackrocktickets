from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^$', 'tickets.txadmin.views.index'),
    (r'^occurrence/(?P<occurrence_id>\d+)/stats/$',
        'tickets.txadmin.views.occurrence_stats'),
)
