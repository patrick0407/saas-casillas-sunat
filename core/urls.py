"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from clientes.views import dashboard_view, lista_rucs_view, crear_ruc_view, login_view, logout_view
from automatizacion.views import bandeja_casilla_view, marcar_leido_view
from clientes.views import configuracion_estudio_view  
from clientes.views import cuenta_suspendida_view
from clientes.views import lista_comprobantes

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('', dashboard_view, name='dashboard'),
    path('rucs/', lista_rucs_view, name='lista_rucs'),
    path('rucs/nuevo/', crear_ruc_view, name='crear_ruc'),
    path('casilla/', bandeja_casilla_view, name='bandeja_casilla'),
    path('casilla/marcar-leido/<int:notificacion_id>/', marcar_leido_view, name='marcar_leido'),
    path('configuracion/', configuracion_estudio_view, name='configuracion_estudio'),
    path('suspendido/', cuenta_suspendida_view, name='cuenta_suspendida'),
    path('comprobantes/', lista_comprobantes, name='lista_comprobantes'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)