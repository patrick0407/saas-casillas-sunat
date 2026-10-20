import os
import time
from datetime import datetime
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
        wait = WebDriverWait(driver, 25)

        # 1. Login SOL SUNAT
        url_sunat = "https://e-menu.sunat.gob.pe/cl-ti-itmenu/MenuInternet.htm"
        for intento in range(3):
            try:
                driver.get(url_sunat)
                break
            except Exception:
                time.sleep(2)

        input_ruc = wait.until(EC.element_to_be_clickable((By.ID, "txtRuc")))
        input_ruc.click()
        input_ruc.clear()
        input_ruc.send_keys(cliente.ruc.strip())

        input_user = driver.find_element(By.ID, "txtUsuario")
        input_user.click()
        input_user.clear()
        input_user.send_keys(cliente.usuario_sol.strip())

        input_pass = driver.find_element(By.ID, "txtContrasena")
        input_pass.click()
        input_pass.clear()
        input_pass.send_keys(cliente.clave_sol.strip())

        btn_aceptar = driver.find_element(By.ID, "btnAceptar")
        driver.execute_script("arguments[0].click();", btn_aceptar)

        time.sleep(5)
        print(f"Sesión iniciada correctamente para el RUC: {cliente.ruc}")

        # Guardar captura de pantalla de verificación
        captura_path = os.path.join(settings.BASE_DIR, 'pantalla_sunat.png')
        driver.save_screenshot(captura_path)

        # 2. Manejo de iFrame de SUNAT si existe
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        if iframes:
            driver.switch_to.frame(iframes[0])

        # 3. Mapeo de la tabla de la Propuesta del RCE (FALABELLA, Mercadolibre, BCP, etc.)
        filas = driver.find_elements(By.XPATH, "//table//tr[td]")
        comprobantes_creados = 0
        for fila in filas:
            cols = fila.find_elements(By.TAG_NAME, "td")
            if len(cols) >= 9:
                fecha_emision = cols[1].text.strip()     # Ej: 04/08/2026
                tipo_cp = cols[3].text.strip()           # Ej: 01
                serie = cols[4].text.strip()             # Ej: F004
                numero = cols[5].text.strip()            # Ej: 244708
                ruc_contraparte = cols[7].text.strip()   # Ej: 20547836473
                razon_social = cols[8].text.strip()      # Ej: FALABELLA.COM S.A.C.
                monto_str = cols[9].text.strip()         # Ej: 28.90

                try:
                    monto = float(monto_str.replace(',', ''))
                except ValueError:
                    monto = 0.0

                try:
                    fecha_obj = datetime.strptime(fecha_emision, "%d/%m/%Y").date()
                except Exception:
                    fecha_obj = timezone.now().date()

                Comprobante.objects.get_or_create(
                    ruc_propietario=cliente.ruc,
                    serie=serie,
                    numero=numero,
                    defaults={
                        'ruc_contraparte': ruc_contraparte,
                        'tipo_comprobante': tipo_cp,
                        'fecha_emision': fecha_obj,
                        'monto_total': monto,
                        'origen': 'RECIBIDO',
                    }
                )
                comprobantes_creados += 1

        print(f"Sincronización finalizada para RUC {cliente.ruc}. Registros guardados: {comprobantes_creados}")

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