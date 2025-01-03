import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import time
import os

# Configurar logger principal
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Configurar el manejador para el archivo
file_handler = logging.FileHandler('robot.log', mode='w')
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# Configurar el manejador para la consola
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# Cargar variables de entorno
from dotenv import load_dotenv
load_dotenv()

USER = os.getenv("PORTAL_USER")
PASSWORD = os.getenv("PORTAL_PASSWORD")
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
SPREADSHEET_ID = "1bGo4MAwjZwVhQmzTjksRoHV6UuaPaYa-UVYB21vL_Ls"
RANGE_NAME = "Principal!A3:G3"

def setup_driver():
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--headless")  # Para ejecución en entornos sin GUI
    options.add_argument("--window-size=1920,1080")
    service = Service("/usr/local/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def login_sistema_requerimientos(driver):
    try:
        logging.info("Navegando al portal de sistema de requerimientos.")
        driver.get("https://sistemaderequerimientos.cl/")

        logging.info("Intentando hacer clic en 'Soy Proveedor'...")
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "tabs-icons-text-2-tab"))
        ).click()
        logging.info("Clic en 'Soy Proveedor' realizado.")

        logging.info("Ingresando credenciales...")
        WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.ID, "inputUsername_recover"))
        ).send_keys(USER)
        driver.find_element(By.ID, "inputPassword_recover").send_keys(PASSWORD)

        logging.info("Intentando hacer clic en 'Iniciar Sesión'...")
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div#tabs-icons-text-2 form button[type='submit']"))
        ).click()
        logging.info("Inicio de sesión realizado.")
        time.sleep(5)

    except Exception as e:
        logging.error(f"Error durante el inicio de sesión: {e}")
        raise

def navegar_menu_soporte_operativo(driver):
    try:
        logging.info("Intentando hacer clic en 'Soporte operativo'...")
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(@class,'dropdown-toggle') and contains(text(),'Soporte operativo')]")
        )).click()
        logging.info("Clic en 'Soporte operativo' realizado.")

        logging.info("Intentando hacer clic en 'Personal Externo'...")
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@href='#module_hrm']//span[contains(text(),'Personal Externo')]")
        )).click()
        logging.info("Clic en 'Personal Externo' realizado.")

        logging.info("Intentando hacer clic en 'Estado de solicitudes Personal Externo'...")
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@href='/workflow/externalizacion-personal' and contains(text(),'Estado de solicitudes Personal Externo')]")
        )).click()
        logging.info("Clic en 'Estado de solicitudes Personal Externo' realizado.")

        time.sleep(2)

    except Exception as e:
        logging.error(f"Error navegando el menú: {e}")
        raise

def ingresar_y_extraer_datos(driver):
    try:
        logging.info("Intentando extraer datos de la solicitud...")

        # Extraer número de la solicitud desde la tabla
        numero_solicitud_element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "td.sorting_1 a.btn.btn-sm.text-orange"))
        )
        numero_solicitud = numero_solicitud_element.text.strip()
        logging.info(f"Número de solicitud extraído: {numero_solicitud}")

        # Hacer clic en el número de la solicitud
        numero_solicitud_element.click()
        logging.info("Clic en el número de la primera solicitud realizado.")
        time.sleep(3)

        # Extraer Cargo solicitado
        cargo = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//strong[contains(text(), 'Cargo solicitado:')]/following-sibling::span"))
        ).text.strip()

        # Extraer Sucursal o Dirección
        sucursal = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//strong[contains(text(), 'Dirección confirmada:')]/following-sibling::span"))
        ).text.strip()

        # Extraer Fecha de Inicio
        fecha_inicio = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//strong[contains(text(), 'Fecha de inicio:')]/following-sibling::span"))
        ).text.strip()

        # Extraer Fecha de Término
        fecha_termino = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//strong[contains(text(), 'Fecha de término:')]/following-sibling::span"))
        ).text.strip()

        # Extraer Causal
        causal = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//strong[contains(text(), 'Causal solicitud:')]/following-sibling::span"))
        ).text.strip()

        # Generar enlace para la solicitud
        link = f"https://sistemaderequerimientos.cl/pe_workflow/externalizacion-personal/{numero_solicitud}"

        # Almacenar todos los datos en un diccionario
        datos = {
            "numero_solicitud": numero_solicitud,
            "cargo": cargo,
            "sucursal": sucursal,
            "fecha_inicio": fecha_inicio,
            "fecha_termino": fecha_termino,
            "causal": causal,
            "link": link
        }
        logging.info(f"Datos extraídos: {datos}")
        return datos

    except Exception as e:
        logging.error(f"Error al extraer datos de la solicitud: {e}")
        raise

def actualizar_google_sheets(datos):
    try:
        logging.info("Intentando actualizar Google Sheets...")
        creds = Credentials.from_service_account_file("service_account.json", scopes=SCOPES)
        service = build("sheets", "v4", credentials=creds)

        # Crear la fila con los datos
        values = [[
            datos["numero_solicitud"],
            datos["cargo"],
            datos["sucursal"],
            datos["fecha_inicio"],
            datos["fecha_termino"],
            datos["causal"],
            datos["link"]
        ]]

        # Preparar el cuerpo de la solicitud
        body = {"values": values}

        # Actualizar las celdas en Google Sheets
        result = service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME,
            valueInputOption="USER_ENTERED",
            body=body,
        ).execute()
        logging.info(f"{result.get('updatedCells')} celda(s) actualizada(s) en Google Sheets.")

    except Exception as e:
        logging.error(f"Error actualizando Google Sheets: {e}")
        raise

def main():
    driver = setup_driver()
    try:
        login_sistema_requerimientos(driver)
        navegar_menu_soporte_operativo(driver)
        datos = ingresar_y_extraer_datos(driver)
        actualizar_google_sheets(datos)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
