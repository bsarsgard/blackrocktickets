from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^$', 'tickets.txadmin.views.index'),
)
