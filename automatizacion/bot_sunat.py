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
from clientes.models import ClienteRuc
from .models import NotificacionCasilla

def procesar_casilla_sunat_invisible(cliente: ClienteRuc):
    # Ruta donde se guardarán los archivos PDF descargados
    download_dir = os.path.join(settings.MEDIA_ROOT, 'notificaciones_pdf')
    os.makedirs(download_dir, exist_ok=True)

    # Configuración de Chrome en modo Headless (Oculto)
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')  # Ejecución 100% invisible en segundo plano
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--window-size=1920,1080')

    # Configuración para descargar PDFs automáticamente sin abrir el visor
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True
    }
    options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 20)

    try:
        # 1. Autenticación en SUNAT
        driver.get("https://e-menu.sunat.gob.pe/cl-ti-itmenu/MenuInternet.htm")

        wait.until(EC.presence_of_element_located((By.ID, "txtRuc"))).send_keys(cliente.ruc)
        driver.find_element(By.ID, "txtUsuario").send_keys(cliente.usuario_sol)
        driver.find_element(By.ID, "txtContrasena").send_keys(cliente.clave_sol)
        driver.find_element(By.ID, "btnAceptar").click()

        time.sleep(3)

        # 2. Aquí Selenium navega por el DOM del Buzón de Notificaciones en segundo plano,
        # guarda los archivos en download_dir y registra las notificaciones en la base de datos.
        
        # Ejemplo de registro al encontrar una notificación con su PDF guardado:
        # NotificacionCasilla.objects.create(
        #     cliente_ruc=cliente,
        #     origen='SUNAT',
        #     codigo_documento='RES-2026-X',
        #     asunto='Notificación Automática',
        #     fecha_emision=timezone.now(),
        #     archivo_pdf='notificaciones_pdf/nombre_archivo.pdf'
        # )

    except Exception as e:
        print(f"Error procesando RUC {cliente.ruc} en segundo plano: {str(e)}")
    finally:
        driver.quit()