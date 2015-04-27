from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView
from app import views
from django.contrib import admin
admin.autodiscover()


urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'app.views.home', name='home'),
    url(r'^admin/', 'app.views.admin', name='admin'),
    url(r'^registro/', 'app.views.registro', name = "registro"),
    url(r'^busqueda/','app.views.busqueda', name = 'busqueda'),
    url(r'^login/', 'app.views.login', name = 'login'),
   	url(r'^pagos/', 'app.views.pagos', name = "pagos"),
    url(r'^auth/', 'app.views.auth', name = "auth"),
    url(r'^logout/', 'app.views.logout', name = "logout"),
    url(r'^exitoso/', 'app.views.exitoso', name = "exitoso"),
    url(r'^registro_guardar/', 'app.views.registro_guardar', name = "registro_guardar"), 
    #url(r'^admin/', include(admin.site.urls)),
)
