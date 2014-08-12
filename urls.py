from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^tickets/', include('tickets.foo.urls')),
    (r'^', include('tickets.texas.urls')),
    (r'^schedules/', include('tickets.txsched.urls')),
    (r'^q/', include('tickets.txqueue.urls')),
    (r'^a/', include('tickets.txadmin.urls')),
    (r'^accounts/login/', 'tickets.texas.views.user_login'),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs'
    # to INSTALLED_APPS to enable admin documentation:
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
)
