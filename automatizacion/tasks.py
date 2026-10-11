from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from clientes.models import ClienteRuc
from .bot_sunat import procesar_casilla_sunat_invisible

def ejecutar_revision_masiva():
    """Recorre todos los RUCs activos y extrae sus notificaciones de SUNAT."""
    print("=== [APScheduler] Iniciando revisión masiva de casillas SUNAT ===")
    rucs = ClienteRuc.objects.all()

    for cliente in rucs:
        try:
            print(f"-> Procesando RUC: {cliente.ruc}")
            procesar_casilla_sunat_invisible(cliente)
        except Exception as e:
            print(f"Error procesando RUC {cliente.ruc}: {str(e)}")

    print("=== [APScheduler] Revisión masiva completada ===")

def iniciar_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), "default")

    # Configura el intervalo de ejecución (ej. cada 2 horas o según necesidad)
    # También se puede usar 'cron' para horas fijas: trigger='cron', hour='8,17'
    scheduler.add_job(
        ejecutar_revision_masiva,
        'interval',
        hours=2,
        id='revision_casillas_sunat',
        replace_existing=True,
    )

    scheduler.start()
    print("-> APScheduler iniciado: Revisión de casillas programada cada 2 horas.")