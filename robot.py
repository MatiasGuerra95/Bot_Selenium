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

# Configurar logging
logging.basicConfig(
    filename='robot.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

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
RANGE_NAME = "Principal!A3:A"

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
            EC.element_to_be_clickable((By.XPATH, "//a[contains(@class,'dropdown-toggle') and contains(text(),'Soporte operativo')]"))
        ).click()
        logging.info("Clic en 'Soporte operativo' realizado.")

        logging.info("Intentando hacer clic en 'Personal Externo'...")
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@href='#module_hrm']//span[contains(text(),'Personal Externo')]"))
        ).click()
        logging.info("Clic en 'Personal Externo' realizado.")

        logging.info("Intentando hacer clic en 'Estado de solicitudes Personal Externo'...")
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@href='/workflow/externalizacion-personal' and contains(text(),'Estado de solicitudes Personal Externo')]"))
        ).click()
        logging.info("Clic en 'Estado de solicitudes Personal Externo' realizado.")

        time.sleep(2)

    except Exception as e:
        logging.error(f"Error navegando el menú: {e}")
        raise

def ingresar_y_extraer_numero(driver):
    try:
        logging.info("Intentando hacer clic en el número de la primera solicitud...")
        numero_link = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "td.sorting_1 a.btn.btn-sm.text-orange"))
        )
        numero_link.click()
        logging.info("Clic en el número de la primera solicitud realizado.")
        time.sleep(3)

        logging.info("Intentando extraer el número de solicitud desde el encabezado de la página...")
        try:
            numero_solicitud_element = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//span[@class='breadcrumb-item active current']"))
            )
            numero_solicitud = numero_solicitud_element.text.replace("Solicitud N°", "").strip()
        except Exception as e:
            logging.warning("No se encontró el número en el breadcrumb, intentando el encabezado principal...")
            numero_solicitud_element = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//h1[contains(@class, 'font-weight-300 mb-0')]")
            ))
            numero_solicitud = numero_solicitud_element.text.split("N°")[-1].strip()

        logging.info(f"Número de solicitud extraído: {numero_solicitud}")
        return numero_solicitud

    except Exception as e:
        logging.error(f"Error al ingresar o extraer el número de solicitud: {e}")
        raise

def actualizar_google_sheets(valor):
    try:
        logging.info("Intentando actualizar Google Sheets...")
        creds = Credentials.from_service_account_file("service_account.json", scopes=SCOPES)
        service = build("sheets", "v4", credentials=creds)
        values = [[valor]]
        body = {"values": values}
        result = service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME,
            valueInputOption="USER_ENTERED",
            body=body,
        ).execute()
        logging.info(f"{result.get('updates').get('updatedCells')} celda(s) actualizada(s) en Google Sheets.")

    except Exception as e:
        logging.error(f"Error actualizando Google Sheets: {e}")
        raise

def main():
    driver = setup_driver()
    try:
        login_sistema_requerimientos(driver)
        navegar_menu_soporte_operativo(driver)
        numero_requerimiento = ingresar_y_extraer_numero(driver)
        actualizar_google_sheets(numero_requerimiento)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()