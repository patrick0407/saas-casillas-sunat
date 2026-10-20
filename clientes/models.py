from django.db import models
from django.contrib.auth.models import User
from .utils import encriptar_texto, desencriptar_texto
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class PerfilEstudio(models.Model):
    # Propietario / Jefe del Estudio Contable
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil_estudio')
    nombre_estudio = models.CharField(max_length=200)
    
    # Asistentes / Colaboradores vinculados
    colaboradores = models.ManyToManyField(User, related_name='estudios_asociados', blank=True)

    # --- CONTROL DE SUSCRIPCIÓN Y PAGOS (SaaS) ---
    estado_pago = models.BooleanField("Suscripción Activa", default=True)
    fecha_vencimiento_pago = models.DateField("Fecha de Vencimiento de Pago", null=True, blank=True)
    limite_colaboradores = models.PositiveIntegerField("Límite de Asistentes Permitidos", default=10)

    # Credenciales SMTP
    email_smtp = models.EmailField("Correo Remitente (Gmail)", blank=True, null=True)
    password_smtp = models.CharField("Contraseña de Aplicación Gmail", max_length=255, blank=True, null=True)
    use_custom_email = models.BooleanField("Usar correo propio para enviar alertas", default=False)

    telefono_whatsapp = models.CharField("Teléfono WhatsApp", max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def suscripcion_valida(self):
        """Devuelve False inmediatamente si estado_pago es False o la fecha ya venció."""
        if not self.estado_pago:
            return False
        if self.fecha_vencimiento_pago and self.fecha_vencimiento_pago < timezone.now().date():
            return False
        return True

    def __str__(self):
        return self.nombre_estudio
    
class ClienteRuc(models.Model):
    estudio = models.ForeignKey(PerfilEstudio, on_delete=models.CASCADE, related_name='rucs')
    razon_social = models.CharField(max_length=200)
    ruc = models.CharField(max_length=11)
    dni_representante = models.CharField(max_length=15, blank=True, null=True)
    
    # Credenciales encriptadas
    usuario_sol = models.CharField(max_length=50)
    _clave_sol = models.CharField(max_length=255, db_column='clave_sol')
    
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    # Propiedad para encriptar/desencriptar la clave de forma transparente
    @property
    def clave_sol(self):
        return desencriptar_texto(self._clave_sol)

    @clave_sol.setter
    def clave_sol(self, raw_password):
        self._clave_sol = encriptar_texto(raw_password)

    def __str__(self):
        return f"{self.ruc} - {self.razon_social}"

class Comprobante(models.Model):
    TIPO_CHOICES = [
        ('01', 'Factura'),
        ('03', 'Boleta de Venta'),
        ('07', 'Nota de Crédito'),
        ('08', 'Nota de Débito'),
    ]
    
    ORIGEN_CHOICES = [
        ('RECIBIDO', 'Recibido (Compras / RCE)'),
        ('EMITIDO', 'Emitido (Ventas / RVE)'),
    ]

    ruc_propietario = models.CharField(max_length=11)  # RUC de tu cliente
    ruc_contraparte = models.CharField(max_length=11)  # RUC del emisor/receptor
    razon_social_contraparte = models.CharField(max_length=255, blank=True, null=True)
    tipo_comprobante = models.CharField(max_length=2, choices=TIPO_CHOICES, default='01')
    serie = models.CharField(max_length=10)
    numero = models.CharField(max_length=20)
    fecha_emision = models.DateField()
    monto_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    origen = models.CharField(max_length=10, choices=ORIGEN_CHOICES, default='RECIBIDO')
    
    # Archivos PDF y XML extraídos de SUNAT
    archivo_pdf = models.FileField(upload_to='comprobantes/pdf/', blank=True, null=True)
    archivo_xml = models.FileField(upload_to='comprobantes/xml/', blank=True, null=True)
    
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_tipo_comprobante_display()} {self.serie}-{self.numero} ({self.ruc_propietario})"