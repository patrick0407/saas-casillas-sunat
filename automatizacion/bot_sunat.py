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

def procesar_casilla_sunat_invisible(cliente: ClienteRuc):
    download_dir = os.path.join(settings.MEDIA_ROOT, 'notificaciones_pdf')
    os.makedirs(download_dir, exist_ok=True)

    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    driver = None
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        wait = WebDriverWait(driver, 30)

        # 1. Login SOL SUNAT
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

        time.sleep(5)
        print(f"Sesión iniciada correctamente para el RUC: {cliente.ruc}")

        # Guardar captura de pantalla justo después del login para inspeccionar
        captura_path = os.path.join(settings.BASE_DIR, 'pantalla_sunat.png')
        driver.save_screenshot(captura_path)
        print(f"Captura guardada en: {captura_path}")

        # Intentar cerrar pop-ups o avisos iniciales de SUNAT si existen
        try:
            btn_cerrar = driver.find_elements(By.XPATH, "//button[contains(text(),'Aceptar') or contains(text(),'Cerrar') or @class='btn-primary']")
            if btn_cerrar:
                btn_cerrar[0].click()
                time.sleep(2)
        except Exception:
            pass

    except Exception as e:
        print(f"Error procesando RUC {cliente.ruc}: {str(e)}")
    finally:
        if driver:
            driver.quit()

def extraer_historial_sire(cliente_ruc_id):
    try:
        cliente = ClienteRuc.objects.get(id=cliente_ruc_id)
        procesar_casilla_sunat_invisible(cliente)
    except Exception as e:
        print(f"Error en extraer_historial_sire para ID {cliente_ruc_id}: {str(e)}")
    download_dir = os.path.join(settings.MEDIA_ROOT, 'notificaciones_pdf')
    os.makedirs(download_dir, exist_ok=True)

    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    driver = None
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        wait = WebDriverWait(driver, 30)

        # 1. Login SOL SUNAT
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

        time.sleep(5)
        print(f"Sesión iniciada correctamente para el RUC: {cliente.ruc}")

        # Guardar captura de pantalla justo después del login para inspeccionar
        captura_path = os.path.join(settings.BASE_DIR, 'pantalla_sunat.png')
        driver.save_screenshot(captura_path)
        print(f"Captura guardada en: {captura_path}")

    except Exception as e:
        print(f"Error procesando RUC {cliente.ruc}: {str(e)}")
    finally:
        if driver:
            driver.quit()

def extraer_historial_sire(cliente_ruc_id):
    try:
        cliente = ClienteRuc.objects.get(id=cliente_ruc_id)
        procesar_casilla_sunat_invisible(cliente)
    except Exception as e:
        print(f"Error en extraer_historial_sire para ID {cliente_ruc_id}: {str(e)}")