from django.core.management.base import BaseCommand
from django.utils import timezone
from clientes.models import ClienteRuc
from automatizacion.models import NotificacionCasilla

class Command(BaseCommand):
    help = 'Simula la extracción de notificaciones de la casilla electrónica'

    def handle(self, *args, **kwargs):
        rucs = ClienteRuc.objects.filter(activo=True)

        if not rucs.exists():
            self.stdout.write(self.style.WARNING("No hay RUCs activos registrados. Registra uno en la web primero."))
            return

        for cliente in rucs:
            self.stdout.write(f"Procesando RUC: {cliente.ruc} ({cliente.razon_social})...")

            # Notificación simulada de SUNAT
            NotificacionCasilla.objects.create(
                cliente_ruc=cliente,
                origen='SUNAT',
                codigo_documento='RES-2026-001234',
                asunto='Resolución de Intendencia - Notificación Coactiva',
                fecha_emision=timezone.now(),
                contenido_resumen='Se notifica la resolución N° 01234 respecto al periodo fiscal 2025-12.',
                leido=False
            )

            # Notificación simulada de SUNAFIL
            NotificacionCasilla.objects.create(
                cliente_ruc=cliente,
                origen='SUNAFIL',
                codigo_documento='INSP-2026-9876',
                asunto='Requerimiento de Información Laboral',
                fecha_emision=timezone.now(),
                contenido_resumen='Solicitud de acreditación de registro de trabajadores en planilla T-Registro.',
                leido=False
            )

            self.stdout.write(self.style.SUCCESS(f"¡Notificaciones registradas exitosamente para RUC {cliente.ruc}!"))