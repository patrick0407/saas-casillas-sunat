from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from clientes import views
from automatizacion.views import bandeja_casilla_view, marcar_leido_view

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Autenticación
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard y RUCs
    path('', views.dashboard_view, name='dashboard'),
    path('rucs/', views.lista_rucs_view, name='lista_rucs'),
    path('rucs/nuevo/', views.crear_ruc_view, name='crear_ruc'),
    
    # Casilla Electrónica
    path('casilla/', bandeja_casilla_view, name='bandeja_casilla'),
    path('casilla/marcar-leido/<int:notificacion_id>/', marcar_leido_view, name='marcar_leido'),
    
    # Configuración y Estado de Cuenta
    path('configuracion/', views.configuracion_estudio_view, name='configuracion_estudio'),
    path('suspendido/', views.cuenta_suspendida_view, name='cuenta_suspendida'),
    
    # SIRE / Comprobantes y Sincronización Manual
    path('comprobantes/', views.lista_comprobantes, name='lista_comprobantes'),
    path('sincronizar-sunat/', views.sincronizar_manual_sunat, name='sincronizar_manual_sunat'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)