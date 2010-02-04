from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^ijat/', include('ijat.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
    
    (r'^eats/$', 'ijat.eats.views.index'),
    (r'^eats/show/(?P<eat_id>\d+)/$', 'ijat.eats.views.show'),
    (r'^eats/new/$', 'ijat.eats.views.new'),
    
    (r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'accounts/login.html'}),

)
