from django.contrib import admin
from .models import ClienteRuc, PerfilEstudio

@admin.register(PerfilEstudio)
class PerfilEstudioAdmin(admin.ModelAdmin):
    # Una única columna 'estado_pago' para activar o desactivar la suscripción completa
    list_display = (
        'nombre_estudio', 
        'usuario', 
        'estado_pago', 
        'fecha_vencimiento_pago', 
        'limite_colaboradores', 
        'created_at'
    )
    # Permite editar el interruptor de pago, la fecha y el límite directamente en la lista
    list_editable = ('estado_pago', 'fecha_vencimiento_pago', 'limite_colaboradores')
    search_fields = ('nombre_estudio', 'usuario__username')
    filter_horizontal = ('colaboradores',)

@admin.register(ClienteRuc)
class ClienteRucAdmin(admin.ModelAdmin):
    list_display = ('ruc', 'razon_social', 'estudio')
    search_fields = ('ruc', 'razon_social')