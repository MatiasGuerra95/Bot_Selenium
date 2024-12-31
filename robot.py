from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from dotenv import load_dotenv
import time
import os

load_dotenv()

USER = os.getenv("PORTAL_USER")
PASSWORD = os.getenv("PORTAL_PASSWORD")

def setup_driver():
    options = Options()
    options.add_argument("--start-maximized")
    
    # Quita comentario para correr en modo headless (sin interfaz)
    # options.add_argument("--headless")

    # Opcional: Usar un User-Agent que parezca más “humano”
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    )

    # Ajusta la ruta a ChromeDriver en tu sistema
    service = Service("/usr/local/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def login_sistema_requerimientos():
    driver = setup_driver()

    try:
        # 1) Ir al portal
        driver.get("https://sistemaderequerimientos.cl/")
        print("Visita inicial a sistemaderequerimientos.cl")
        time.sleep(3)  # Espera que cargue

        driver.save_screenshot("paso_0_landing.png")

        # 2) Clic en "Soy Proveedor"
        boton_proveedor = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "tabs-icons-text-2-tab"))
        )
        boton_proveedor.click()
        print("Clic en 'Soy Proveedor' exitoso.")
        time.sleep(2)

        driver.save_screenshot("paso_1_soy_proveedor.png")

        # 3) Ingresar usuario
        username_field = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, "inputUsername_recover"))
        )
        username_field.clear()
        username_field.send_keys(USER)
        print("Usuario ingresado.")
        time.sleep(1)

        # 4) Ingresar contraseña
        password_field = driver.find_element(By.ID, "inputPassword_recover")
        password_field.clear()
        password_field.send_keys(PASSWORD)
        print("Contraseña ingresada.")
        time.sleep(1)

        driver.save_screenshot("paso_2_credenciales_llenadas.png")

        # 5) Buscar el botón "Iniciar Sesión" dentro del tab Proveedores
        boton_iniciar = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((
                By.CSS_SELECTOR,
                "div#tabs-icons-text-2.tab-pane.fade.active.show form button[type='submit']"
            ))
        )
        # Asegurar que sea clicable
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((
                By.CSS_SELECTOR,
                "div#tabs-icons-text-2.tab-pane.fade.active.show form button[type='submit']"
            ))
        )

        # Hacemos scroll hasta el botón
        driver.execute_script("arguments[0].scrollIntoView(true);", boton_iniciar)
        time.sleep(1)

        # Forzamos el clic vía JS
        driver.execute_script("arguments[0].click();", boton_iniciar)
        print("Clic en 'Iniciar Sesión' (Proveedores) realizado.")
        time.sleep(5)  # Esperar la respuesta del servidor

        driver.save_screenshot("paso_3_despues_login.png")
        print("HTML tras dar clic en Iniciar Sesión (parcial):")
        print(driver.page_source[:1000])  # Muestra solo primeros 1000 chars

        # Retornamos el driver, ya logueado
        return driver

    except Exception as e:
        print(f"Error durante login: {e}")
        driver.save_screenshot("error_login.png")
        print("Screenshot guardada: error_login.png")
        driver.quit()
        return None

def navegar_menu_soporte_operativo(driver):
    """
    Navega en el menú:
    1) Soporte operativo
    2) Personal Externo
    3) Estado de solicitudes Personal Externo
    Ajusta los XPATH según tu HTML real (texto exacto).
    """
    try:
        # 1) Clic en "Soporte operativo"
        soporte_operativo = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//a[@class='nav-link btn btn-default-a dropdown-toggle' and contains(text(),'Soporte operativo')]"
            ))
        )
        soporte_operativo.click()
        print("Clic en 'Soporte operativo'")
        time.sleep(1)

        # 2) Clic en "Personal Externo"
        personal_externo = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//a[@href='#module_hrm' and contains(@class,'nav-link')]//span[contains(text(),'Personal Externo')]"
            ))
        )
        personal_externo.click()
        print("Clic en 'Personal Externo'")
        time.sleep(1)

        # 3) Esperar a que se expanda la sección #module_hrm
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div#module_hrm.menu_level_2.collapse.show"))
        )
        print("Sección #module_hrm expandida.")

        # 4) Clic en "Estado de solicitudes Personal Externo"
        estado_solicitudes = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//a[@href='/workflow/externalizacion-personal' and contains(@class,'nav-link') "
                "and contains(text(),'Estado de solicitudes Personal Externo')]"
            ))
        )
        estado_solicitudes.click()
        print("Clic en 'Estado de solicitudes Personal Externo'.")
        time.sleep(2)

        driver.save_screenshot("despues_menu_soporte.png")
        print("¡Navegación completa hacia Estado de solicitudes Personal Externo!")
    
    except Exception as e:
        print(f"Error navegando menú: {e}")
        driver.save_screenshot("error_menu.png")

def ingresar_solicitud_40502(driver):
    """
    Hace clic en la solicitud #40502 (número naranja) dentro de la tabla,
    cuya etiqueta <a> tenga href="/pe_workflow/externalizacion-personal/40502"
    o texto '40502'.
    """
    try:
        # Esperar el enlace "40502"
        solicitud_40502_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//a[@href='/pe_workflow/externalizacion-personal/40502' and contains(text(),'40502')]"
            ))
        )
        solicitud_40502_link.click()
        print("Clic en la solicitud #40502 (número naranja).")
        time.sleep(3)
        
        # Si abre en nueva pestaña, podrías cambiar el foco:
        # windows = driver.window_handles
        # driver.switch_to.window(windows[-1])
        # time.sleep(2)

        driver.save_screenshot("paso_ingresar_40502.png")

    except Exception as e:
        print(f"Error al ingresar a la solicitud 40502: {e}")
        driver.save_screenshot("error_40502.png")


def main():
    # 1) Login
    driver = login_sistema_requerimientos()
    if driver is not None:
        try:
            # 2) Navegar menú
            navegar_menu_soporte_operativo(driver)
            time.sleep(2)

            # 3) Ingresar a la solicitud #40502
            ingresar_solicitud_40502(driver)
            time.sleep(2)

        finally:
            # Al terminar, cierra el navegador (o déjalo abierto para inspeccionar)
            driver.quit()

if __name__ == "__main__":
    main()

