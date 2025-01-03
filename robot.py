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
SPREADSHEET_ID = "1bGo4MAwjZwVhQmzTjksRoHV6UuaPaYa-UVYB21vL_Ls"
RANGE_NAME = "Principal!A3:A"

def setup_driver():
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--headless")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--window-size=1920,1080")
    service = Service("/usr/local/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def login_sistema_requerimientos(driver):
    try:
        driver.get("https://sistemaderequerimientos.cl/")
        print("Navegando al portal de sistema de requerimientos.")
        
        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.ID, "tabs-icons-text-2-tab"))
        ).click()
        print("Clic en 'Soy Proveedor'.")
        
        WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located((By.ID, "inputUsername_recover"))
        ).send_keys(USER)
        
        driver.find_element(By.ID, "inputPassword_recover").send_keys(PASSWORD)
        
        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div#tabs-icons-text-2 form button[type='submit']"))
        ).click()
        print("Inicio de sesión realizado.")
        time.sleep(5)
    except Exception as e:
        print(f"Error durante el inicio de sesión: {e}")
        driver.save_screenshot("error_login.png")
        raise

def navegar_menu_soporte_operativo(driver):
    try:
        print("Intentando hacer clic en 'Soporte operativo'...")
        soporte_operativo = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'Soporte operativo')]"))
        )
        soporte_operativo.click()
        print("Clic en 'Soporte operativo' realizado.")
        time.sleep(2)  # Espera para que se despliegue el submenú

        print("Intentando hacer clic en 'Personal Externo'...")
        personal_externo = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@href='#module_hrm' and contains(@class, 'nav-link')]"))
        )
        personal_externo.click()
        print("Clic en 'Personal Externo' realizado.")
        time.sleep(2)  # Espera para que se expanda el submenú correspondiente

        print("Intentando hacer clic en 'Estado de solicitudes Personal Externo'...")
        estado_solicitudes = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@href='/workflow/externalizacion-personal' and contains(@class, 'nav-link')]"))
        )
        estado_solicitudes.click()
        print("Clic en 'Estado de solicitudes Personal Externo' realizado.")
        time.sleep(2)  # Espera para que cargue la página

    except Exception as e:
        print(f"Error navegando el menú: {e}")
        driver.save_screenshot("error_navegando_menu.png")
        print("HTML actual del DOM:")
        print(driver.page_source[:1000])  # Captura el HTML para inspección
        raise


def ingresar_y_extraer_numero(driver):
    try:
        print("Intentando ingresar a la solicitud desde la tabla...")

        # Esperar y localizar el enlace del primer número de solicitud
        numero_enlace = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//table[@id='dt_review']//tbody/tr[1]/td[1]/a[contains(@class, 'btn-sm text-orange')]"))
        )
        print("Enlace del número de solicitud encontrado.")
        numero_enlace.click()
        print("Ingreso a la solicitud realizado.")

        # Esperar a que la página interna cargue y localizar el número
        WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "span.breadcrumb-item.active.current"))
        )
        numero_detalle = driver.find_element(By.CSS_SELECTOR, "span.breadcrumb-item.active.current").text
        print(f"Número de solicitud extraído: {numero_detalle.strip()}")
        return numero_detalle.strip()
    except Exception as e:
        print(f"Error al ingresar o extraer el número de solicitud: {e}")
        # Guardar el HTML del DOM actual para depuración
        with open("dom_error.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print("HTML actual del DOM guardado en 'dom_error.html'")
        raise


def actualizar_google_sheets(valor):
    try:
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
        print(f"{result.get('updates').get('updatedCells')} celda(s) actualizada(s) en Google Sheets.")
    except Exception as e:
        print(f"Error actualizando Google Sheets: {e}")
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
