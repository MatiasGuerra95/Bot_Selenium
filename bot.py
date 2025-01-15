import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
    StaleElementReferenceException
)
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import time
import os

# Configurar logger principal
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)  # Cambiado a DEBUG para obtener más detalles

# Configurar el manejador para el archivo
file_handler = logging.FileHandler('robot.log', mode='w')
file_handler.setLevel(logging.DEBUG)  # Cambiado a DEBUG
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
RANGE_NAME = "En proceso!A3:S3"

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

def extraer_texto_con_reintentos(driver, xpath, default="N/A", intentos=3, delay=2):
    """
    Intenta extraer el texto de un elemento por XPath con reintentos en caso de excepciones.

    :param driver: Instancia de Selenium WebDriver.
    :param xpath: Selector XPath del elemento.
    :param default: Valor por defecto si el elemento no se encuentra.
    :param intentos: Número de intentos de reintento.
    :param delay: Tiempo de espera entre intentos en segundos.
    :return: Texto extraído o el valor predeterminado.
    """
    for intento in range(intentos):
        try:
            elemento = WebDriverWait(driver, 15).until(  # Aumentar timeout a 15
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            texto = elemento.text.strip() if elemento else default
            if texto == default:
                # Log adicional para depuración
                html_content = elemento.get_attribute('outerHTML') if elemento else 'Elemento no encontrado'
                logger.debug(f"Elemento encontrado para XPath: {xpath}. HTML: {html_content}")
            return texto
        except (TimeoutException, StaleElementReferenceException) as e:
            logger.warning(f"Intento {intento + 1} fallido para XPath: {xpath}. Error: {e}")
            time.sleep(delay)
    # Log adicional si todos los intentos fallan
    logger.error(f"No se pudo extraer el texto para XPath: {xpath} después de {intentos} intentos.")
    return default

def navegar_menu_soporte_operativo(driver):
    try:
        logger.info("Intentando hacer clic en 'Soporte operativo'...")
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(@class,'dropdown-toggle') and contains(text(),'Soporte operativo')]"))
        ).click()
        logger.info("Clic en 'Soporte operativo' realizado.")

        logger.info("Intentando hacer clic en 'Personal Externo'...")
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@href='#module_hrm']//span[contains(text(),'Personal Externo')]"))
        ).click()
        logger.info("Clic en 'Personal Externo' realizado.")

        logger.info("Intentando hacer clic en 'Estado de solicitudes Personal Externo'...")
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@href='/workflow/externalizacion-personal' and contains(text(),'Estado de solicitudes Personal Externo')]"))
        ).click()
        logger.info("Clic en 'Estado de solicitudes Personal Externo' realizado.")

        # Añadir clic para acceder a "En Proceso"
        logger.info("Intentando hacer clic en 'En Proceso'...")
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "tabs-icons-text-2-tab"))
        ).click()
        logger.info("Clic en 'En Proceso' realizado.")

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
        return False

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

def capturar_pantalla(driver, nombre_archivo):
    """
    Captura una captura de pantalla y la guarda con el nombre especificado.
    """
    try:
        logger.info(f"Captura de pantalla guardada: {nombre_archivo}")
    except Exception as e:
        logger.error(f"No se pudo guardar la captura de pantalla {nombre_archivo}: {e}")

def ingresar_y_extraer_todas_las_solicitudes(driver):
    """
    Extrae los datos de todas las solicitudes en "En Proceso", manejando la paginación.
    """
    try:
        logger.info("Iniciando extracción de solicitudes en proceso con paginación...")
        solicitudes = []
        pagina_actual = 1

        # Asegúrate de que este ID coincida con el del botón "Siguiente" real en tu HTML
        next_button_id = "table-dt_process_next"

        while True:
            logger.info(f"Procesando página {pagina_actual} de solicitudes en proceso...")

            # 1. Esperar (o simplemente buscar) las filas de la tabla en la página actual
            filas_solicitudes = driver.find_elements(
                By.CSS_SELECTOR, "td.sorting_1 a.btn.btn-sm.text-orange"
            )

            if not filas_solicitudes:
                logger.warning(f"No se encontraron solicitudes en la página {pagina_actual}. Terminando paginación.")
                break

            logger.info(f"Se encontraron {len(filas_solicitudes)} solicitudes en la página {pagina_actual}.")

            # 2. Iterar sobre cada fila (cada solicitud)
            for solicitud_element in filas_solicitudes:
                numero_solicitud = solicitud_element.text.strip()
                if not numero_solicitud:
                    logger.warning("Número de solicitud vacío. Continuando con la siguiente fila.")
                    continue

                logger.info(f"Número de solicitud: {numero_solicitud}")

                # Abrir la solicitud en una nueva pestaña
                original_window = driver.current_window_handle
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", solicitud_element)
                    driver.execute_script("arguments[0].click();", solicitud_element)
                    time.sleep(2)

                    # Esperar la nueva pestaña
                    WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(2))
                    ventanas = driver.window_handles
                    nueva_pestana = [w for w in ventanas if w != original_window][0]
                    driver.switch_to.window(nueva_pestana)
                    logger.info(f"Cambio a la pestaña {nueva_pestana}")

                    # Extraer la información
                    datos, secciones = ingresar_y_extraer_datos(driver, numero_solicitud)
                    if datos and secciones:
                        solicitudes.append((datos, secciones))
                        logger.info(f"Solicitud {numero_solicitud} añadida a la lista.")
                    else:
                        logger.warning(f"Datos incompletos para la solicitud {numero_solicitud}.")

                except Exception as e:
                    logger.error(f"Error procesando solicitud {numero_solicitud}: {e}")
                    capturar_pantalla(driver, f"error_solicitud_{numero_solicitud}.png")
                    # Cerrar la(s) pestaña(s) extra y volver a la original
                    for wh in driver.window_handles:
                        if wh != original_window:
                            driver.switch_to.window(wh)
                            driver.close()
                    driver.switch_to.window(original_window)

            # 3. Intentar ir a la siguiente página
            # Buscar el botón "Siguiente" por ID o un selector alternativo
            try:
                next_button = driver.find_element(By.ID, next_button_id)
            except NoSuchElementException:
                logger.debug("No se encontró el botón por ID. Probando selector alternativo (.next:not(.disabled))...")
                next_buttons = driver.find_elements(
                    By.CSS_SELECTOR, "li.paginate_button.next:not(.disabled)"
                )
                if not next_buttons:
                    logger.info("No hay botón 'Siguiente' habilitado. Fin de paginación.")
                    break
                next_button = next_buttons[0]

            # Verificar si está deshabilitado por clase
            if "disabled" in next_button.get_attribute("class"):
                logger.info("Botón 'Siguiente' deshabilitado. No hay más páginas.")
                break

            # 4. Hacer clic en el botón "Siguiente"
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
            driver.execute_script("arguments[0].click();", next_button)
            logger.info("Clic en 'Siguiente' realizado.")

            # 5. Esperar un poco para que la tabla se recargue
            time.sleep(2)

            # 6. Subir el número de página y repetir el bucle
            pagina_actual += 1

        logger.info(f"Extracción completa. Total de solicitudes: {len(solicitudes)}.")
        return solicitudes

    except Exception as e:
        logger.error(f"Error en la extracción de todas las solicitudes: {e}")
        capturar_pantalla(driver, "error_extraer_todas_solicitudes.png")
        return []

def extraer_tabla_aceptacion_proveedor(driver):
    try:
        logger.info("Verificando la tabla dentro de 'Aceptación del proveedor'.")

        # XPath para localizar la tabla directamente
        xpath_tabla = "//div[contains(@class, 'list-group-item text-sm')]//table[@class='table table-bordered']"
        
        # Esperar a que la tabla esté presente
        tabla = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, xpath_tabla))
        )
        logger.info("Tabla localizada. Extrayendo datos...")

        # Extraer las filas de la tabla
        filas = tabla.find_elements(By.XPATH, ".//tbody/tr")
        datos_tabla = [[columna.text.strip() for columna in fila.find_elements(By.TAG_NAME, "td")] for fila in filas]
        
        logger.info(f"Datos extraídos de la tabla: {datos_tabla}")
        return datos_tabla

    except TimeoutException:
        logger.error("Timeout al esperar la tabla de 'Aceptación del proveedor'. Verifica el XPath y el tiempo de carga.")
        return None
    except Exception as e:
        logger.error(f"Error al extraer la tabla de 'Aceptación del proveedor': {e}")
        return None

def ingresar_y_extraer_datos(driver, numero_solicitud):
    """
    Extrae los datos de una solicitud específica.

    :param driver: Instancia de Selenium WebDriver.
    :param numero_solicitud: Número de la solicitud a extraer.
    :return: Tuple (datos, secciones) o (None, None) en caso de fallo.
    """
    try:
        logger.info(f"Intentando extraer datos para la solicitud: {numero_solicitud}")

        # Verificar y hacer clic en 'Datos de la solicitud'
        datos_clickeados = localizar_y_clickeador_datos_solicitud(driver)
        if not datos_clickeados:
            logger.warning(f"No se pudo hacer clic en 'Datos de la solicitud' para la solicitud: {numero_solicitud}")
            return None, None

        # Extraer los campos específicos
        cargo = extraer_texto_con_reintentos(driver, "//div[contains(@id, 'datos_solicitud') and contains(@class, 'show')]//strong[contains(text(), 'Cargo solicitado:')]/following-sibling::span")
        sucursal = extraer_texto_con_reintentos(driver, "//div[contains(@id, 'datos_solicitud') and contains(@class, 'show')]//strong[contains(text(), 'Dirección confirmada:')]/following-sibling::span")
        fecha_inicio = extraer_texto_con_reintentos(driver, "//div[contains(@id, 'datos_solicitud') and contains(@class, 'show')]//strong[contains(text(), 'Fecha de inicio:')]/following-sibling::span")
        fecha_termino = extraer_texto_con_reintentos(driver, "//div[contains(@id, 'datos_solicitud') and contains(@class, 'show')]//strong[contains(text(), 'Fecha de término:')]/following-sibling::span")
        causal = extraer_texto_con_reintentos(driver, "//div[contains(@id, 'datos_solicitud') and contains(@class, 'show')]//strong[contains(text(), 'Causal solicitud:')]/following-sibling::span")
        observaciones = extraer_texto_con_reintentos(driver, "//div[contains(@id, 'datos_solicitud') and contains(@class, 'show')]//strong[contains(text(), 'Observaciones:')]/following-sibling::span")

        # Generar enlace para la solicitud
        link = f"https://sistemaderequerimientos.cl/pe_workflow/externalizacion-personal/{numero_solicitud}"

        # Detectar las secciones en la nueva pestaña
        secciones = detectar_secciones(driver)

        # Extraer la tabla de 'Aceptación del proveedor'
        tabla_aceptacion = None
        if secciones.get("aceptacion_proveedor", False):
            logger.info("Intentando extraer la tabla de 'Aceptación del proveedor'.")
            tabla_aceptacion = extraer_tabla_aceptacion_proveedor(driver)
            if not tabla_aceptacion:
                logger.warning(f"No se encontraron datos en la tabla de 'Aceptación del proveedor' para la solicitud: {numero_solicitud}")

        # Validar los datos extraídos
        if not cargo or not sucursal or not fecha_inicio or not fecha_termino:
            logger.warning(f"Datos incompletos extraídos para la solicitud {numero_solicitud}. Validación requerida.")

        # Almacenar todos los datos en un diccionario
        datos = {
            "numero_solicitud": numero_solicitud,
            "cargo": cargo,
            "sucursal": sucursal,
            "fecha_inicio": fecha_inicio,
            "fecha_termino": fecha_termino,
            "causal": causal,
            "observaciones": observaciones,
            "link": link,
            "tabla_aceptacion_proveedor": tabla_aceptacion,  # Agregar los datos de la tabla aquí
        }

        logger.info(f"Datos extraídos: {datos}")
        return datos, secciones  # Retorna el diccionario con los datos

    except Exception as e:
        logger.error(f"Error al extraer datos de la solicitud {numero_solicitud}: {e}")
        capturar_pantalla(driver, f"error_extraccion_{numero_solicitud}.png")
        return None, None
    finally:
        # Cerrar la pestaña de la solicitud y volver a la original
        try:
            original_window = driver.window_handles[0]
            driver.close()
            if original_window in driver.window_handles:
                driver.switch_to.window(original_window)
                logger.info("Cerrada la pestaña de la solicitud y vuelto a la pestaña original.")
            else:
                logger.error("No se pudo volver a la pestaña original.")
        except Exception as e:
            logger.error(f"Error al cerrar la pestaña de la solicitud: {e}")



def limpiar_google_sheet(spreadsheet_id, rango, intentos=3, delay=5):
    """
    Limpia el contenido de un rango específico en Google Sheets, sin afectar los encabezados.
    
    :param spreadsheet_id: ID de la hoja de cálculo en Google Drive.
    :param rango: Rango en Google Sheets donde limpiar los datos (A3:Q, por ejemplo).
    :param intentos: Número de intentos en caso de fallo.
    :param delay: Tiempo de espera entre intentos.
    """
    try:
        creds = Credentials.from_service_account_file("service_account.json", scopes=SCOPES)
        service = build("sheets", "v4", credentials=creds)

        for intento in range(intentos):
            try:
                # Borrar los valores del rango (A3:Q hacia abajo)
                service.spreadsheets().values().clear(
                    spreadsheetId=spreadsheet_id,
                    range=rango
                ).execute()

                logger.info(f"Contenido del rango '{rango}' eliminado correctamente.")
                break
            except Exception as e:
                logger.error(f"Error limpiando rango '{rango}' en Google Sheets (intento {intento+1}): {e}")
                if intento < intentos - 1:
                    time.sleep(delay)
                else:
                    raise

    except Exception as e:
        logger.error(f"Error configurando la limpieza de Google Sheets: {e}")
        raise


def actualizar_google_sheets_batch(solicitudes, rango, intentos=3, delay=5):
    """
    Sube todas las solicitudes a Google Sheets en una sola solicitud con reintentos.

    :param solicitudes: Lista de tuplas (datos, secciones).
    :param rango: Rango en Google Sheets donde agregar los datos.
    :param intentos: Número de intentos de reintento en caso de fallo.
    :param delay: Tiempo de espera entre intentos en segundos.
    """
    try:
        if not solicitudes:
            logger.error("No hay datos para actualizar en Google Sheets.")
            return

        # Limpieza del rango específico
        logger.info(f"Limpiando el rango '{rango}' en Google Sheets antes de insertar nuevos datos...")
        limpiar_google_sheet(SPREADSHEET_ID, rango)

        # Configuración de credenciales
        creds = Credentials.from_service_account_file("service_account.json", scopes=SCOPES)
        service = build("sheets", "v4", credentials=creds)

        # Crear lista de valores para todas las solicitudes
        values = []
        for datos, secciones in solicitudes:
            # Datos básicos de la solicitud
            base_row = [
                datos.get("numero_solicitud", ""),
                "",
                datos.get("cargo", ""),
                datos.get("sucursal", ""),
                datos.get("fecha_inicio", ""),
                datos.get("fecha_termino", ""),
                datos.get("causal", ""),
                datos.get("observaciones", ""),
                "",
                datos.get("link", ""),
                "Sí" if secciones.get("boton_aceptar", False) else "No",
                "Sí" if secciones.get("datos_solicitud", False) else "No",
                "Sí" if secciones.get("aceptacion_evaluador_rrhh", False) else "No",
                "Sí" if secciones.get("proveedor_seleccionado", False) else "No",
                "Sí" if secciones.get("aceptacion_proveedor", False) else "No",
                "Sí" if secciones.get("cierre_automatico", False) else "No",
                "Sí" if secciones.get("rechazos_proveedores", False) else "No",
                "Sí" if secciones.get("reasignacion_solicitudes", False) else "No"
            ]

            # Extraer y agregar las filas de la tabla
            tabla = datos.get("tabla_aceptacion_proveedor", [])
            if tabla:
                for fila in tabla:
                    # Combina la fila base con cada fila de la tabla
                    values.append(base_row + fila)
            else:
                # Si no hay tabla, simplemente agrega la fila base
                values.append(base_row)

        # Preparar el cuerpo de la solicitud
        body = {"values": values}

        for intento in range(intentos):
            try:
                result = service.spreadsheets().values().append(
                    spreadsheetId=SPREADSHEET_ID,
                    range=rango,
                    valueInputOption="USER_ENTERED",
                    insertDataOption="INSERT_ROWS",
                    body=body
                ).execute()

                logger.info(f"Se subieron {result['updates']['updatedRows']} filas a Google Sheets correctamente.")
                break

            except Exception as e:
                logger.error(f"Error subiendo datos a Google Sheets en el intento {intento + 1}: {e}")
                if intento < intentos - 1:
                    time.sleep(delay)
                else:
                    raise

    except Exception as e:
        logger.error(f"Error subiendo datos a Google Sheets: {e}")
        raise




def actualizar_google_sheets(datos, secciones):
    """
    Sube una sola solicitud a Google Sheets.

    :param datos: Diccionario con los datos extraídos.
    :param secciones: Diccionario con el estado de las secciones.
    """
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
            range="En Proceso!A:S",  # Rango donde agregar los datos
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
        # Paso 1: Iniciar sesión
        login_sistema_requerimientos(driver)

        # Paso 2: Navegar
        navegar_menu_soporte_operativo(driver)

        # Paso 3: Extraer todas las solicitudes sin límite
        todas_las_solicitudes = ingresar_y_extraer_todas_las_solicitudes(driver)

        # Paso 4: Subir datos agrupados a Google Sheets
        actualizar_google_sheets_batch(todas_las_solicitudes, "En Proceso!A3:S")

    except Exception as e:
        logger.error(f"Proceso terminado con errores: {e}")
    finally:
        try:
            driver.quit()
            logger.info("Driver cerrado.")
        except Exception as e:
            logger.error(f"Error al cerrar el driver: {e}")

if __name__ == "__main__":
    main()
