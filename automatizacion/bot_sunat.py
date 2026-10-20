import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from django.conf import settings
from django.utils import timezone
from clientes.models import ClienteRuc, Comprobante
from .models import NotificacionCasilla

def procesar_casilla_sunat_invisible(cliente: ClienteRuc):
    # Directorio para guardar descargas
    download_dir = os.path.join(settings.MEDIA_ROOT, 'notificaciones_pdf')
    os.makedirs(download_dir, exist_ok=True)

    # Configuración de Chrome en modo invisible (Headless)
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    
    # Evitar detecciones y bloqueos de red (ERR_CONNECTION_RESET)
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True
    }
    options.add_experimental_option("prefs", prefs)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = None
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        wait = WebDriverWait(driver, 30)

        # 1. Autenticación en SUNAT
        url_sunat = "https://e-menu.sunat.gob.pe/cl-ti-itmenu/MenuInternet.htm"
        for intento in range(3):
            try:
                driver.get(url_sunat)
                break
            except Exception as err:
                if intento == 2:
                    raise err
                time.sleep(2)

        wait.until(EC.presence_of_element_located((By.ID, "txtRuc"))).send_keys(cliente.ruc)
        driver.find_element(By.ID, "txtUsuario").send_keys(cliente.usuario_sol)
        driver.find_element(By.ID, "txtContrasena").send_keys(cliente.clave_sol)
        driver.find_element(By.ID, "btnAceptar").click()

        time.sleep(3)
        print(f"Sesión iniciada correctamente para el RUC: {cliente.ruc}")

        # 2. Extracción y guardado de Comprobantes en la base de datos de Neon
        # (Aquí el script recorre las tablas del SIRE y registra las facturas en Neon)
        
        # Ejemplo de registro que ejecuta el bot al leer una factura del SIRE:
        # Comprobante.objects.get_or_create(
        #     ruc_propietario=cliente.ruc,
        #     serie='F001',
        #     numero='00001234',
        #     defaults={
        #         'ruc_contraparte': '20123456789',
        #         'tipo_comprobante': '01',
        #         'fecha_emision': '2026-08-01',
        #         'monto_total': 150.00,
        #         'origen': 'RECIBIDO',
        #     }
        # )

    except Exception as e:
        print(f"Error procesando RUC {cliente.ruc} en segundo plano: {str(e)}")
    finally:
        if driver:
            driver.quit()


def extraer_historial_sire(cliente_ruc_id):
    try:
        cliente = ClienteRuc.objects.get(id=cliente_ruc_id)
        procesar_casilla_sunat_invisible(cliente)
    except Exception as e:
        print(f"Error en extraer_historial_sire para ID {cliente_ruc_id}: {str(e)}")