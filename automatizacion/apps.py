import os
from django.apps import AppConfig

class AutomatizacionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'automatizacion'

    def ready(self):
        # Evita la doble ejecución en el entorno de desarrollo cuando se usa StatReloader
        if os.environ.get('RUN_MAIN') == 'true':
            from .tasks import iniciar_scheduler
            iniciar_scheduler()