from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^$', 'tickets.txqueue.views.index'),
    (r'^q/$', 'tickets.txqueue.views.index'),
    (r'^check/(?P<code>.+)/$', 'tickets.txqueue.views.check_code'),
    (r'^use/(?P<code>.+)/$', 'tickets.txqueue.views.use_code'),
)
