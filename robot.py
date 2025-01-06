import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException
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
RANGE_NAME = "Principal!A3:Q3"

def setup_driver():
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # options.add_argument("--headless")  # Para ejecución en entornos sin GUI
    options.add_argument("--window-size=1920,1080")
    service = Service("/usr/local/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def login_sistema_requerimientos(driver):
    try:
        logger.info("Navegando al portal de sistema de requerimientos.")
        driver.get("https://sistemaderequerimientos.cl/")

        logger.info("Intentando hacer clic en 'Soy Proveedor'...")
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "tabs-icons-text-2-tab"))
        ).click()
        logger.info("Clic en 'Soy Proveedor' realizado.")

        logger.info("Ingresando credenciales...")
        WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.ID, "inputUsername_recover"))
        ).send_keys(USER)
        driver.find_element(By.ID, "inputPassword_recover").send_keys(PASSWORD)

        logger.info("Intentando hacer clic en 'Iniciar Sesión'...")
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div#tabs-icons-text-2 form button[type='submit']"))
        ).click()
        logger.info("Inicio de sesión realizado.")
        time.sleep(5)

    except Exception as e:
        logger.error(f"Error durante el inicio de sesión: {e}")
        raise

def extraer_texto_xpath(driver, xpath, default="N/A"):
    """
    Extrae el texto de un elemento localizado por XPath. Si no encuentra el elemento, retorna un valor predeterminado.
    """
    try:
        elemento = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        return elemento.text.strip() if elemento else default
    except TimeoutException:
        logger.warning(f"No se encontró el elemento para XPath: {xpath}")
        return default


def navegar_menu_soporte_operativo(driver):
    try:
        logger.info("Intentando hacer clic en 'Soporte operativo'...")
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(@class,'dropdown-toggle') and contains(text(),'Soporte operativo')]")
        )).click()
        logger.info("Clic en 'Soporte operativo' realizado.")

        logger.info("Intentando hacer clic en 'Personal Externo'...")
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@href='#module_hrm']//span[contains(text(),'Personal Externo')]")
        )).click()
        logger.info("Clic en 'Personal Externo' realizado.")

        logger.info("Intentando hacer clic en 'Estado de solicitudes Personal Externo'...")
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@href='/workflow/externalizacion-personal' and contains(text(),'Estado de solicitudes Personal Externo')]")
        )).click()
        logger.info("Clic en 'Estado de solicitudes Personal Externo' realizado.")

        time.sleep(2)

    except Exception as e:
        logger.error(f"Error navegando el menú: {e}")
        raise

def localizar_y_clickeador_datos_solicitud(driver, timeout=30):
    try:
        xpath = "//div[@data-metakey='datos_solicitud']//div[@role='button' and contains(@class, 'collapseHeader')]"
        datos_solicitud_button = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", datos_solicitud_button)
        time.sleep(1)  # Dar tiempo para que se estabilice

        # Intentar con ActionChains y fallback con JavaScript
        try:
            ActionChains(driver).move_to_element(datos_solicitud_button).click().perform()
            logger.info("Clic realizado usando ActionChains.")
        except Exception as e:
            logger.warning(f"ActionChains falló: {e}. Intentando con JavaScript.")
            driver.execute_script("arguments[0].click();", datos_solicitud_button)
            logger.info("Clic realizado usando JavaScript.")

        # Confirmar que el botón se expandió
        WebDriverWait(driver, 10).until(
            lambda d: datos_solicitud_button.get_attribute("aria-expanded") == "true"
        )
        logger.info("Botón 'Datos de la solicitud' expandido correctamente.")
        return True
    except Exception as e:
        logger.error(f"No se pudo localizar o hacer clic en 'Datos de la solicitud': {e}")
        driver.save_screenshot("error_click_datos_solicitud.png")
        return False

def revisar_errores_consola(driver):
    """
    Revisa y registra los errores en la consola del navegador.
    """
    try:
        logs = driver.get_log('browser')
        for log_entry in logs:
            if log_entry['level'] == 'SEVERE':
                logger.warning(f"Error de la consola: {log_entry}")
    except Exception as e:
        logger.error(f"No se pudo obtener los logs de la consola del navegador: {e}")

def capturar_pantalla(driver, nombre_archivo):
    """
    Captura una captura de pantalla y la guarda con el nombre especificado.
    """
    try:
        driver.save_screenshot(nombre_archivo)
        logger.info(f"Captura de pantalla guardada: {nombre_archivo}")
    except Exception as e:
        logger.error(f"No se pudo guardar la captura de pantalla {nombre_archivo}: {e}")

def esperar_a_modal_cerrado(driver, timeout=30):
    """
    Espera a que el modal de carga esté cerrado.
    """
    try:
        WebDriverWait(driver, timeout).until(
            EC.invisibility_of_element_located((By.ID, "model-loading"))
        )
        logger.info("Modal de carga cerrado.")
    except TimeoutException:
        logger.warning("El modal de carga sigue visible después del tiempo de espera.")

def detectar_secciones(driver):
    """
    Detecta la presencia de secciones clave y devuelve un diccionario con True/False.
    """
    secciones = {
        "boton_aceptar": False,
        "datos_solicitud": False,
        "aceptacion_evaluador_rrhh": False,
        "proveedor_seleccionado": False,
        "aceptacion_proveedor": False,
        "cierre_automatico": False,
        "rechazos_proveedores": False,
        "reasignacion_solicitudes": False
    }

    try:
        # Verificar cada sección usando sus selectores
        if driver.find_elements(By.CSS_SELECTOR, "button.btn-outline-success[data-target='#form-modal-aceptarSolicitudYOT-aceptacion_ot']"):
            secciones["boton_aceptar"] = True

        if driver.find_elements(By.XPATH, "//div[@data-metakey='datos_solicitud']"):
            secciones["datos_solicitud"] = True

        if driver.find_elements(By.XPATH, "//div[@data-metakey='aceptacion_evaluador_rrhh']"):
            secciones["aceptacion_evaluador_rrhh"] = True

        if driver.find_elements(By.XPATH, "//div[@data-metakey='proveedor_seleccionado']"):
            secciones["proveedor_seleccionado"] = True

        if driver.find_elements(By.XPATH, "//div[@data-metakey='confirmacion_personal_a_enviar']"):
            secciones["aceptacion_proveedor"] = True

        if driver.find_elements(By.XPATH, "//div[@data-metakey='cierre_automatico']"):
            secciones["cierre_automatico"] = True

        if driver.find_elements(By.XPATH, "//div[@data-metakey='rechazo_proveedor']"):
            secciones["rechazos_proveedores"] = True

        if driver.find_elements(By.XPATH, "//div[@data-metakey='anulacion_ot']"):
            secciones["reasignacion_solicitudes"] = True

    except Exception as e:
        logger.error(f"Error detectando secciones: {e}")

    logger.info(f"Secciones detectadas: {secciones}")
    return secciones

def ingresar_y_extraer_datos(driver):
    try:
        logger.info("Intentando extraer datos de la solicitud...")

        # Guardar el handle de la pestaña original
        original_window = driver.current_window_handle
        logger.info(f"Handle de la pestaña original: {original_window}")

        # Extraer número de la solicitud desde la tabla
        numero_solicitud_element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "td.sorting_1 a.btn.btn-sm.text-orange"))
        )
        numero_solicitud = numero_solicitud_element.text.strip()
        logger.info(f"Número de solicitud extraído: {numero_solicitud}")

        # Hacer clic en el número de la solicitud que abre una nueva pestaña
        numero_solicitud_element.click()
        logger.info("Clic en el número de la primera solicitud realizado.")
        time.sleep(3)  # Espera para que la nueva pestaña se abra

        # Esperar a que se abra una nueva pestaña
        WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(2))
        logger.info("Nueva pestaña abierta.")

        # Obtener todos los handles de las ventanas
        ventanas = driver.window_handles
        logger.info(f"Handles de ventanas abiertas: {ventanas}")

        # Identificar la nueva pestaña
        nueva_pestana = [window for window in ventanas if window != original_window][0]
        logger.info(f"Handle de la nueva pestaña: {nueva_pestana}")

        # Cambiar el foco a la nueva pestaña
        driver.switch_to.window(nueva_pestana)
        logger.info("Cambio de foco a la nueva pestaña realizado.")

        # Verificar el título o la URL para asegurar que estamos en la pestaña correcta
        titulo = driver.title
        logger.info(f"Título de la nueva pestaña: {titulo}")

        url = driver.current_url
        logger.info(f"URL de la nueva pestaña: {url}")

        # Verificar que estamos en la URL esperada
        expected_url_fragment = "/pe_workflow/externalizacion-personal/"
        if expected_url_fragment not in url:
            logger.error("La nueva pestaña no corresponde a la URL esperada.")
            raise Exception("Cambio de pestaña fallido.")

        # Esperar a que la página de la nueva pestaña cargue completamente
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//div[@data-metakey='datos_solicitud']"))
        )
        logger.info("Página de la nueva pestaña cargada exitosamente.")

        # Llamar a la función para localizar y hacer clic en 'Datos de la solicitud'
        datos_clickeados = localizar_y_clickeador_datos_solicitud(driver)

        if datos_clickeados:
            logger.info("Clic en 'Datos de la solicitud' realizado con éxito.")
            # Extraer datos específicos después de expandir
            # Asegúrate de ajustar los selectores según el HTML real
            cargo_element = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@id, 'datos_solicitud') and contains(@class, 'show')]//strong[contains(text(), 'Cargo solicitado:')]/following-sibling::span"))
            )
            cargo = cargo_element.text.strip() if cargo_element else "N/A"

            sucursal_element = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@id, 'datos_solicitud') and contains(@class, 'show')]//strong[contains(text(), 'Dirección confirmada:')]/following-sibling::span"))
            )
            sucursal = sucursal_element.text.strip() if sucursal_element else "N/A"

            fecha_inicio_element = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@id, 'datos_solicitud') and contains(@class, 'show')]//strong[contains(text(), 'Fecha de inicio:')]/following-sibling::span"))
            )
            fecha_inicio = fecha_inicio_element.text.strip() if fecha_inicio_element else "N/A"

            fecha_termino_element = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@id, 'datos_solicitud') and contains(@class, 'show')]//strong[contains(text(), 'Fecha de término:')]/following-sibling::span"))
            )
            fecha_termino = fecha_termino_element.text.strip() if fecha_termino_element else "N/A"

            causal_element = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@id, 'datos_solicitud') and contains(@class, 'show')]//strong[contains(text(), 'Causal solicitud:')]/following-sibling::span"))
            )
            causal = causal_element.text.strip() if causal_element else "N/A"

            # Generar enlace para la solicitud
            link = f"https://sistemaderequerimientos.cl/pe_workflow/externalizacion-personal/{numero_solicitud}"

            # Detectar las secciones en la nueva pestaña
            secciones = detectar_secciones(driver)

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
            logger.info(f"Datos extraídos: {datos}")
            return datos, secciones  # Retorna el diccionario con los datos

        else:
            logger.error("No se pudo realizar el clic en 'Datos de la solicitud'.")
            return None  # Retorna None en caso de fallo

    except Exception as e:
        logger.error(f"Error durante la extracción de datos: {e}")
        capturar_pantalla(driver, "error_ingresar_y_extraer_datos.png")
        return None
    
def ingresar_y_extraer_todas_las_solicitudes(driver):
    """
    Extrae los datos de todas las solicitudes disponibles en la tabla, manejando la paginación.
    """
    try:
        logger.info("Intentando extraer datos de todas las solicitudes disponibles con paginación...")
        solicitudes = []  # Lista para almacenar los datos de todas las solicitudes

        while True:  # Bucle para iterar por cada página
            # Obtener todos los elementos que representan las solicitudes en la tabla
            filas_solicitudes = WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "td.sorting_1 a.btn.btn-sm.text-orange"))
            )
            logger.info(f"Se encontraron {len(filas_solicitudes)} solicitudes en la tabla.")

            for index, solicitud_element in enumerate(filas_solicitudes):
                try:
                    logger.info(f"Procesando solicitud {index + 1} en la página actual...")

                    # Guardar el handle de la pestaña original
                    original_window = driver.current_window_handle

                    # Hacer clic en el número de la solicitud para abrir una nueva pestaña
                    driver.execute_script("arguments[0].click();", solicitud_element)
                    logger.info("Clic en el número de la solicitud realizado.")
                    time.sleep(3)

                    # Esperar a que se abra una nueva pestaña
                    WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(2))

                    # Cambiar el foco a la nueva pestaña
                    ventanas = driver.window_handles
                    nueva_pestana = [window for window in ventanas if window != original_window][0]
                    driver.switch_to.window(nueva_pestana)

                    # Extraer datos de la solicitud actual
                    datos_clickeados = localizar_y_clickeador_datos_solicitud(driver)
                    if datos_clickeados:
                        cargo = extraer_texto_xpath(driver, "//div[contains(@id, 'datos_solicitud') and contains(@class, 'show')]//strong[contains(text(), 'Cargo solicitado:')]/following-sibling::span")
                        sucursal = extraer_texto_xpath(driver, "//div[contains(@id, 'datos_solicitud') and contains(@class, 'show')]//strong[contains(text(), 'Dirección confirmada:')]/following-sibling::span")
                        fecha_inicio = extraer_texto_xpath(driver, "//div[contains(@id, 'datos_solicitud') and contains(@class, 'show')]//strong[contains(text(), 'Fecha de inicio:')]/following-sibling::span")
                        fecha_termino = extraer_texto_xpath(driver, "//div[contains(@id, 'datos_solicitud') and contains(@class, 'show')]//strong[contains(text(), 'Fecha de término:')]/following-sibling::span")
                        causal = extraer_texto_xpath(driver, "//div[contains(@id, 'datos_solicitud') and contains(@class, 'show')]//strong[contains(text(), 'Causal solicitud:')]/following-sibling::span")

                        # Generar enlace para la solicitud
                        numero_solicitud = extraer_texto_xpath(driver, "//span[contains(@class, 'badge badge-info')]")
                        link = f"https://sistemaderequerimientos.cl/pe_workflow/externalizacion-personal/{numero_solicitud}"

                        # Detectar las secciones en la nueva pestaña
                        secciones = detectar_secciones(driver)

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

                        logger.info(f"Datos extraídos para la solicitud {index + 1}: {datos}")
                        solicitudes.append((datos, secciones))
                    else:
                        logger.error(f"No se pudo extraer datos para la solicitud {index + 1}.")

                    # Cerrar la pestaña actual y volver a la pestaña original
                    driver.close()
                    driver.switch_to.window(original_window)

                except Exception as e:
                    logger.error(f"Error al procesar la solicitud {index + 1}: {e}")
                    capturar_pantalla(driver, f"error_solicitud_{index + 1}.png")
                    continue

            # Intentar pasar a la siguiente página
            try:
                next_button = driver.find_element(By.ID, "table-dt_review_next")
                if "disabled" in next_button.get_attribute("class"):
                    logger.info("No hay más páginas disponibles.")
                    break  # Salir del bucle si no hay más páginas
                else:
                    logger.info("Pasando a la siguiente página...")
                    next_button.click()
                    time.sleep(3)  # Esperar a que la nueva página cargue
            except NoSuchElementException:
                logger.info("Botón 'Siguiente' no encontrado. Terminando proceso de paginación.")
                break

        logger.info(f"Se completó la extracción de todas las solicitudes. Total: {len(solicitudes)} solicitudes.")
        return solicitudes

    except Exception as e:
        logger.error(f"Error durante la extracción de todas las solicitudes: {e}")
        capturar_pantalla(driver, "error_extraer_todas_solicitudes.png")
        return []


def actualizar_google_sheets(datos, secciones):
    try:
        if not datos:
            logger.error("No hay datos para actualizar en Google Sheets.")
            return

        logger.info("Intentando actualizar Google Sheets...")
        creds = Credentials.from_service_account_file("service_account.json", scopes=SCOPES)
        service = build("sheets", "v4", credentials=creds)

        # Crear la fila con los datos en las columnas específicas
        values = [[
            datos.get("numero_solicitud", ""),  # Columna A
            "",  # Columna B vacía
            datos.get("cargo", ""),  # Columna C
            datos.get("sucursal", ""),  # Columna D
            datos.get("fecha_inicio", ""),  # Columna E
            datos.get("fecha_termino", ""),  # Columna F
            datos.get("causal", ""),  # Columna G
            "",  # Columna H vacía
            datos.get("link", ""),  # Columna I
            "Sí" if secciones.get("boton_aceptar", False) else "No",  # Columna J
            "Sí" if secciones.get("datos_solicitud", False) else "No",  # Columna K
            "Sí" if secciones.get("aceptacion_evaluador_rrhh", False) else "No",  # Columna L
            "Sí" if secciones.get("proveedor_seleccionado", False) else "No",  # Columna M
            "Sí" if secciones.get("aceptacion_proveedor", False) else "No",  # Columna N
            "Sí" if secciones.get("cierre_automatico", False) else "No",  # Columna O
            "Sí" if secciones.get("rechazos_proveedores", False) else "No",  # Columna P
            "Sí" if secciones.get("reasignacion_solicitudes", False) else "No"  # Columna Q
        ]]

        # Preparar el cuerpo de la solicitud
        body = {"values": values}

        # Usar la API para añadir la fila al final
        result = service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range="Principal!A:Q",  # Rango donde agregar los datos
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",  # Insertar nuevas filas
            body=body
        ).execute()

        logger.info(f"Se añadió una nueva fila en Google Sheets.")
    except Exception as e:
        logger.error(f"Error actualizando Google Sheets: {e}")
        raise

def main():
    driver = setup_driver()
    try:
        # Paso 1: Iniciar sesión en el sistema de requerimientos
        login_sistema_requerimientos(driver)

        # Paso 2: Navegar por el menú hasta la sección requerida
        navegar_menu_soporte_operativo(driver)

        # Paso 3: Extraer datos de todas las solicitudes
        todas_las_solicitudes = ingresar_y_extraer_todas_las_solicitudes(driver)

        # Paso 4: Actualizar Google Sheets para cada solicitud
        for datos, secciones in todas_las_solicitudes:
            actualizar_google_sheets(datos, secciones)

    except Exception as e:
        logger.error(f"Proceso terminado con errores: {e}")
    finally:
        # Cerrar el driver
        driver.quit()
        logger.info("Driver cerrado.")

if __name__ == "__main__":
    main()
