from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^$', 'tickets.txsched.views.index'),
    url(r'^(?P<schedule_id>\d+)/(?P<sign_up_id>\d+)/$',
        'tickets.txsched.views.schedule', name='schedule'),
    url(r'^sign_up/(?P<sign_up_id>\d+)/admin/$',
        'tickets.txsched.views.sign_up_admin'),
)
