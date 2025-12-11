import base64
import io
import re
import time

from PIL import Image
from pyzbar.pyzbar import decode as qr_decode
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from core.environment.host import get_host_for_selenium_testing
from core.selenium.common import close_driver, initialize_driver


# HELPERS
def login_user(driver, host, email, password):
    """Navega a la página de login, introduce credenciales y envía el formulario."""
    driver.get(f"{host}/login")
    time.sleep(2)
    driver.find_element(By.NAME, "email").send_keys(email)
    driver.find_element(By.NAME, "password").send_keys(password + Keys.RETURN)
    time.sleep(3)


def get_secret_from_qr_image(driver):
    """
    Extrae el secreto BASE32 del código QR visible en la página.
    Requiere las librerías Pillow y pyzbar.
    """
    qr_img_element = driver.find_element(By.XPATH, "//img[contains(@src, 'base64,')]")
    qr_src = qr_img_element.get_attribute("src")

    # Extraer y decodificar el Base64
    base64_data = qr_src.split("base64,")[1]
    image_data = base64.b64decode(base64_data)

    # Abrir la imagen desde bytes y decodificar el código QR
    qr_image = Image.open(io.BytesIO(image_data))

    # Decodificar la URI del QR
    decoded_qr = qr_decode(qr_image)

    if not decoded_qr:
        raise ValueError("QR code could not be decoded from the image.")

    # Extraer la URI y el Secret
    uri = decoded_qr[0].data.decode("utf-8")

    # La URI TOTP tiene el formato: otpauth://totp/ISSUER:USER?secret=BASE32_CODE
    secret_match = re.search(r"secret=([A-Z2-7]{16,})", uri)

    if not secret_match:
        raise ValueError(f"Secret not found in the decoded URI: {uri}")

    return secret_match.group(1)


# Profile Summary loads after login
def test_profile_summary_loads():
    driver = initialize_driver()
    host = get_host_for_selenium_testing()

    try:
        login_user(driver, host, "user1@example.com", "1234")

        driver.get(f"{host}/profile/summary")
        time.sleep(3)

        # Verificar que el perfil se ha cargado correctamente (buscando el nombre del usuario 'John Doe' del seeder)
        driver.find_element(
            By.XPATH,
            "//*[contains(text(), 'John Doe') or contains(text(), 'John') and contains(text(), 'Doe')]",
        )

        print("Test passed! (test_profile_summary_loads)")

    except NoSuchElementException:
        raise AssertionError(
            "Profile summary page did not load or the user data is missing."
        )

    finally:
        close_driver(driver)


# Edit Profile form loads
def test_edit_profile_form_loads():
    driver = initialize_driver()
    host = get_host_for_selenium_testing()

    try:
        login_user(driver, host, "user1@example.com", "1234")

        driver.get(f"{host}/profile/edit")
        time.sleep(3)

        driver.find_element(By.NAME, "name")
        driver.find_element(By.NAME, "surname")

        print("Test passed! (test_edit_profile_form_loads)")

    except NoSuchElementException:
        raise AssertionError("Edit Profile form did not load correctly.")

    finally:
        close_driver(driver)


# Edit Profile success
def test_edit_profile_success():
    driver = initialize_driver()
    host = get_host_for_selenium_testing()

    # Datos para actualizar
    new_name = (
        "NewNameUpdated"  # Cambiamos un poco los datos para asegurar la actualización
    )
    new_surname = "NewSurnameUpdated"
    new_orcid = "0000-0002-1825-0000"
    new_affiliation = "Tech University Updated"

    try:
        # 1. Login
        login_user(driver, host, "user1@example.com", "1234")

        # 2. Navegar a la página de edición
        driver.get(f"{host}/profile/edit")
        time.sleep(5)

        # 3. Rellenar los campos
        driver.find_element(By.NAME, "name").clear()
        driver.find_element(By.NAME, "name").send_keys(new_name)

        driver.find_element(By.NAME, "surname").clear()
        driver.find_element(By.NAME, "surname").send_keys(new_surname)

        driver.find_element(By.NAME, "orcid").clear()
        driver.find_element(By.NAME, "orcid").send_keys(new_orcid)

        driver.find_element(By.NAME, "affiliation").clear()
        driver.find_element(By.NAME, "affiliation").send_keys(new_affiliation)

        # 4. ENVIAR FORMULARIO
        driver.find_element(By.NAME, "submit").click()
        time.sleep(4)

        current_url = driver.current_url

        assert current_url.endswith("/profile/edit"), (
            f"Unexpected redirection to: {current_url}. Expected to stay on /profile/edit"
        )

        driver.find_element(
            By.XPATH, "//*[contains(text(), 'Profile updated successfully')]"
        )

        name_value = driver.find_element(By.NAME, "name").get_attribute("value")
        surname_value = driver.find_element(By.NAME, "surname").get_attribute("value")
        affiliation_value = driver.find_element(By.NAME, "affiliation").get_attribute(
            "value"
        )
        orcid_value = driver.find_element(By.NAME, "orcid").get_attribute("value")

        assert name_value == new_name, (
            f"Name not updated in form field. Expected: {new_name}, Got: {name_value}"
        )
        assert surname_value == new_surname, (
            f"Surname not updated in form field. Expected: {new_surname}, Got: {surname_value}"
        )
        assert affiliation_value == new_affiliation, (
            f"Affiliation not updated in form field. Expected: {new_affiliation}, Got: {affiliation_value}"
        )
        assert orcid_value == new_orcid, (
            f"ORCID not updated in form field. Expected: {new_orcid}, Got: {orcid_value}"
        )

        print(
            "Test passed! (test_edit_profile_success) - Verified update in form fields."
        )

    except AssertionError as e:
        # Captura todos los errores
        raise AssertionError(f"Profile update failed: {e}")

    except NoSuchElementException as e:
        # Esto captura errores de elementos no encontrados
        raise AssertionError(f"Test failed due to missing element: {e.msg}")

    finally:
        close_driver(driver)


# Enable 2FA redirects to QR page and generates secret
def test_enable_2fa_page_loads_and_retrieves_secret():
    driver = initialize_driver()
    host = get_host_for_selenium_testing()

    try:
        login_user(driver, host, "user1@example.com", "1234")

        driver.get(f"{host}/profile/enable-2fa")
        time.sleep(3)

        # Verifica que la página de configuración 2FA se carga (campo token)
        driver.find_element(By.XPATH, "//input[@name='token']")

        # EXTRAER EL SECRET USANDO EL CÓDIGO QR
        secret = get_secret_from_qr_image(driver)

        assert len(secret) > 15, "Retrieved secret length is too short."

        print("Test passed! (test_enable_2fa_page_loads_and_retrieves_secret)")
        return secret

    except NoSuchElementException:
        raise AssertionError(
            "2FA enable page did not load or is missing key elements (token input or QR image)."
        )
    except ValueError as e:
        raise AssertionError(f"2FA QR code processing failed: {e}")

    finally:
        close_driver(driver)


# Disable 2FA works
def test_disable_2fa_works():
    """
    Este test ASUME que el 2FA fue habilitado por el TEST 5.
    """
    driver = initialize_driver()
    host = get_host_for_selenium_testing()

    try:
        login_user(driver, host, "user1@example.com", "1234")

        driver.get(f"{host}/profile/disable-2fa")
        time.sleep(3)

        driver.find_element(
            By.XPATH, "//*[contains(text(), '2FA authentication disabled!')]"
        )
        assert driver.current_url.endswith("/profile/summary")

        print("Test passed! (test_disable_2fa_works)")

    except NoSuchElementException:
        raise AssertionError(
            "2FA disable failed or success message/redirect not found."
        )

    finally:
        close_driver(driver)


# Call the test functions
test_profile_summary_loads()
test_edit_profile_form_loads()
test_edit_profile_success()
test_enable_2fa_page_loads_and_retrieves_secret()
test_disable_2fa_works()
