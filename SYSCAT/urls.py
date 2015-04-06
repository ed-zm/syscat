from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', TemplateView.as_view(template_name= 'index.html'), name='home'),
    #url(r'^blog/', include('blog.urls')),
    url(r'^registro/', TemplateView.as_view(template_name = 'static/templates/registro.html'), name = 'registro'),
    url(r'^busqueda/', TemplateView.as_view(template_name = 'static/templates/busqueda.html'), name = 'busqueda'),
    url(r'^login/', TemplateView.as_view(template_name = 'login.html'), name = 'login'),
                       
    url(r'^admin/', include(admin.site.urls)),
)
