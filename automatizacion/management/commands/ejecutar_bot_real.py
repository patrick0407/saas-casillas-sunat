import time
from django.core.management.base import BaseCommand
from clientes.models import ClienteRuc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class Command(BaseCommand):
    help = 'Abre el navegador e ingresa a SOL SUNAT con las credenciales del RUC'

    def handle(self, *args, **kwargs):
        # Tomamos el primer RUC registrado en la base de datos
        cliente = ClienteRuc.objects.filter(activo=True).first()

        if not cliente:
            self.stdout.write(self.style.ERROR("No hay RUCs registrados en la base de datos."))
            return

        self.stdout.write(self.style.SUCCESS(f"Iniciando Bot para el RUC: {cliente.ruc} ({cliente.razon_social})"))

        options = webdriver.ChromeOptions()
        options.add_argument('--start-maximized')
        # Descomenta la línea de abajo solo si quieres que corra sin abrir ventana visible:
        # options.add_argument('--headless')

        # Inicia Chrome con el driver automático
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        wait = WebDriverWait(driver, 20)

        try:
            self.stdout.write("Navegando a la página de SOL SUNAT...")
            driver.get("https://e-menu.sunat.gob.pe/cl-ti-itmenu/MenuInternet.htm")

            # Espera a que cargue el campo de RUC e ingresa credenciales
            self.stdout.write("Ingresando credenciales SOL...")
            wait.until(EC.presence_of_element_located((By.ID, "txtRuc"))).send_keys(cliente.ruc)
            driver.find_element(By.ID, "txtUsuario").send_keys(cliente.usuario_sol)
            
            # Utiliza la propiedad desencriptada en tiempo de ejecución
            driver.find_element(By.ID, "txtContrasena").send_keys(cliente.clave_sol)

            # Clic en Iniciar Sesión
            driver.find_element(By.ID, "btnAceptar").click()

            self.stdout.write(self.style.SUCCESS("Formulario enviado. Esperando respuesta de SUNAT..."))
            time.sleep(10)  # Mantiene la ventana abierta 10 segundos para observar el resultado

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ocurrió un error durante la automatización: {str(e)}"))
        finally:
            driver.quit()
            self.stdout.write(self.style.SUCCESS("Navegador cerrado."))