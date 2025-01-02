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

# Cargar variables de entorno
from dotenv import load_dotenv
load_dotenv()

USER = os.getenv("PORTAL_USER")
PASSWORD = os.getenv("PORTAL_PASSWORD")
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
SPREADSHEET_ID = "1bGo4MAwjZwVhQmzTjksRoHV6UuaPaYa-UVYB21vL_Ls"  # Reemplaza con el ID de tu Google Sheet
RANGE_NAME = "Principal!A3:A"  # Rango donde agregar el dato SRC

def setup_driver():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--headless")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-extensions")

    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    )

    service = Service("/usr/local/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def login_sistema_requerimientos(driver):
    try:
        driver.get("https://sistemaderequerimientos.cl/")
        print("Visita inicial a sistemaderequerimientos.cl")
        time.sleep(3)

        boton_proveedor = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "tabs-icons-text-2-tab"))
        )
        boton_proveedor.click()
        print("Clic en 'Soy Proveedor'")
        time.sleep(2)

        username_field = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, "inputUsername_recover"))
        )
        username_field.clear()
        username_field.send_keys(USER)

        password_field = driver.find_element(By.ID, "inputPassword_recover")
        password_field.clear()
        password_field.send_keys(PASSWORD)

        boton_iniciar = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div#tabs-icons-text-2 form button[type='submit']"))
        )
        boton_iniciar.click()
        print("Inicio de sesión exitoso")
        time.sleep(5)

    except Exception as e:
        print(f"Error durante login: {e}")
        driver.quit()
        raise

def navegar_menu_soporte_operativo(driver):
    try:
        soporte_operativo = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'Soporte operativo')]"))
        )
        soporte_operativo.click()
        print("Clic en 'Soporte operativo'")
        time.sleep(1)

        personal_externo = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Personal Externo')]/.."))
        )
        personal_externo.click()
        print("Clic en 'Personal Externo'")
        time.sleep(1)

        estado_solicitudes = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'Estado de solicitudes Personal Externo')]")
        ))
        estado_solicitudes.click()
        print("Clic en 'Estado de solicitudes Personal Externo'")
        time.sleep(2)

    except Exception as e:
        print(f"Error navegando el menú: {e}")
        driver.quit()
        raise

def extraer_numero_requerimiento(driver):
    try:
        numero_requerimiento = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, "//table[@id='dt_review']//tbody/tr[1]/td[1]/a"))
        ).text
        print(f"Número de requerimiento encontrado: {numero_requerimiento}")
        return numero_requerimiento
    except Exception as e:
        print(f"Error al extraer el número de requerimiento: {e}")
        driver.quit()
        raise

def actualizar_google_sheets(valor):
    creds = Credentials.from_service_account_file(
        "service_account.json", scopes=SCOPES
    )
    service = build("sheets", "v4", credentials=creds)

    values = [[valor]]
    body = {"values": values}

    result = service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=RANGE_NAME,
        valueInputOption="USER_ENTERED",
        body=body,
    ).execute()
    print(f"{result.get('updates').get('updatedCells')} celda(s) actualizada(s) en Google Sheets.")

def main():
    driver = setup_driver()
    try:
        login_sistema_requerimientos(driver)
        navegar_menu_soporte_operativo(driver)

        numero_requerimiento = extraer_numero_requerimiento(driver)
        actualizar_google_sheets(numero_requerimiento)

    finally:
        driver.quit()

if __name__ == "__main__":
    main()

