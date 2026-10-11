from django.db import models
from clientes.models import ClienteRuc

class NotificacionCasilla(models.Model):
    ORIGEN_CHOICES = [
        ('SUNAT', 'SUNAT'),
        ('SUNAFIL', 'SUNAFIL'),
    ]

    cliente_ruc = models.ForeignKey(ClienteRuc, on_delete=models.CASCADE, related_name='notificaciones')
    origen = models.CharField(max_length=20, choices=ORIGEN_CHOICES, default='SUNAT')
    codigo_documento = models.CharField(max_length=100, blank=True, null=True)
    asunto = models.CharField(max_length=255)
    fecha_emision = models.DateTimeField()
    contenido_resumen = models.TextField(blank=True, null=True)
    archivo_pdf = models.FileField(upload_to='notificaciones_pdf/', blank=True, null=True)
    
    leido = models.BooleanField(default=False)
    fecha_descarga = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_emision']

    def __str__(self):
        return f"[{self.origen}] {self.cliente_ruc.ruc} - {self.asunto}"