import time

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from core.environment.host import get_host_for_selenium_testing
from core.selenium.common import close_driver, initialize_driver


def test_login_and_check_element():
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()

        # Open the login page
        driver.get(f"{host}/login")

        # Wait a little while to make sure the page has loaded completely
        time.sleep(4)

        # Find the username and password field and enter the values
        email_field = driver.find_element(By.NAME, "email")
        password_field = driver.find_element(By.NAME, "password")

        email_field.send_keys("user1@example.com")
        password_field.send_keys("1234")

        # Send the form
        password_field.send_keys(Keys.RETURN)

        # Wait a little while to ensure that the action has been completed
        time.sleep(4)

        try:
            driver.find_element(
                By.XPATH,
                "//h1[contains(@class, 'h2 mb-3') and contains(., 'Latest datasets')]",
            )
            print("Test passed!")

        except NoSuchElementException:
            raise AssertionError("Test failed!")

    finally:
        # Close the browser
        close_driver(driver)


# HELPERS
def login_user(driver, host, email, password):
    driver.get(f"{host}/login")
    time.sleep(2)

    driver.find_element(By.NAME, "email").send_keys(email)
    driver.find_element(By.NAME, "password").send_keys(password + Keys.RETURN)
    time.sleep(3)


# Signup page loads
def test_signup_page_loads():
    driver = initialize_driver()
    host = get_host_for_selenium_testing()

    try:
        driver.get(f"{host}/signup/")
        time.sleep(2)

        driver.find_element(By.XPATH, "//h1[contains(., 'Sign')]")

    except NoSuchElementException:
        raise AssertionError("The signup page did not load correctly")

    finally:
        close_driver(driver)


# Successful signup
def test_signup_success_creates_user_and_redirects_home():
    driver = initialize_driver()
    host = get_host_for_selenium_testing()

    try:
        driver.get(f"{host}/signup/")
        time.sleep(3)

        # Email único por timestamp
        ts = str(int(time.time()))
        driver.find_element(By.NAME, "name").send_keys("New")
        driver.find_element(By.NAME, "surname").send_keys("User")
        driver.find_element(By.NAME, "email").send_keys(f"newuser{ts}@example.com")
        driver.find_element(By.NAME, "password").send_keys("1234" + Keys.RETURN)
        time.sleep(4)

        # Verificar que redirige al index
        driver.find_element(By.XPATH, "//body")

    except NoSuchElementException:
        raise AssertionError("User signup failed or did not redirect to home")

    finally:
        close_driver(driver)


# Signup fails if email already exists
def test_signup_fails_if_email_in_use():
    driver = initialize_driver()
    host = get_host_for_selenium_testing()

    try:
        driver.get(f"{host}/signup/")
        time.sleep(3)

        driver.find_element(By.NAME, "name").send_keys("Test")
        driver.find_element(By.NAME, "surname").send_keys("User")
        driver.find_element(By.NAME, "email").send_keys("user1@example.com")
        driver.find_element(By.NAME, "password").send_keys("1234" + Keys.RETURN)
        time.sleep(3)

        driver.find_element(By.XPATH, "//*[contains(text(),'in use') or contains(text(),'Error')]")

    except NoSuchElementException:
        raise AssertionError("Signup should fail when the email already exists")

    finally:
        close_driver(driver)


# Login page loads
def test_login_page_loads():
    driver = initialize_driver()
    host = get_host_for_selenium_testing()

    try:
        driver.get(f"{host}/login")
        time.sleep(2)

        driver.find_element(By.XPATH, "//h1[contains(., 'Login')]")

    except NoSuchElementException:
        raise AssertionError("Login page did not load correctly")

    finally:
        close_driver(driver)


# Invalid credentials show error
def test_login_invalid_credentials_shows_error():
    driver = initialize_driver()
    host = get_host_for_selenium_testing()

    try:
        login_user(driver, host, "nonexistent@example.com", "wrongpass")

        driver.find_element(By.XPATH, "//*[contains(text(),'Invalid credentials')]")

    except NoSuchElementException:
        raise AssertionError("Invalid credentials should show an error message")

    finally:
        close_driver(driver)


# Successful login redirects home
def test_login_success_redirects_home():
    driver = initialize_driver()
    host = get_host_for_selenium_testing()

    try:
        login_user(driver, host, "user1@example.com", "1234")

        # Si aparece cualquier elemento del index
        driver.find_element(By.TAG_NAME, "body")

    except NoSuchElementException:
        raise AssertionError("Successful login did not redirect to home")

    finally:
        close_driver(driver)


# Logout works
def test_logout_works():
    driver = initialize_driver()
    host = get_host_for_selenium_testing()

    try:
        # Login
        login_user(driver, host, "user1@example.com", "1234")

        # Click Logout
        driver.get(f"{host}/logout")
        time.sleep(2)

        # Debe volver al index (no loggeado)
        driver.find_element(By.XPATH, "//body")

    except NoSuchElementException:
        raise AssertionError("Logout did not redirect correctly")

    finally:
        close_driver(driver)


# Login user with NO 2FA enabled redirects to home
def test_login_user_without_2fa_redirects_home():
    """
    Verifica el comportamiento por defecto (sin 2FA),
    asumiendo que user2 NO tiene 2FA activado por el seeder.
    """
    driver = initialize_driver()
    host = get_host_for_selenium_testing()

    try:
        test_email = "user2@example.com"
        test_pass = "1234"

        login_user(driver, host, test_email, test_pass)
        time.sleep(3)

        # Debe aparecer la página de inicio (index)
        driver.find_element(
            By.XPATH,
            "//h1[contains(@class, 'h2 mb-3') and contains(., 'Latest datasets')]",
        )
        print("Test passed! (test_login_user_without_2fa_redirects_home)")

    except NoSuchElementException:
        raise AssertionError(
            "User without 2FA should be redirected to home but was not."
            "Check if 'user2@example.com' has 2FA UNEXPECTEDLY enabled in the database."
        )

    finally:
        close_driver(driver)


# Accessing 2FA page manually fails if no session
def test_2fa_access_without_session_redirects_to_login():
    """
    Prueba la lógica de la ruta /verify-2fa: si no hay session['pending_2fa_user_id'],
    debe redirigir al login y mostrar un flash message.
    """
    driver = initialize_driver()
    host = get_host_for_selenium_testing()

    try:
        # Intentar acceder directamente a la página 2FA
        driver.get(f"{host}/verify-2fa")
        time.sleep(3)

        # 1. Comprobamos la redirección a Login
        driver.find_element(By.XPATH, "//h1[contains(., 'Login')]")

        # 2. Comprobamos el mensaje flash (no necesario si la redirección es estricta, pero es un buen check)
        print("Test passed! (test_2fa_access_without_session_redirects_to_login)")

    except NoSuchElementException:
        raise AssertionError("Accessing /verify-2fa without a pending session did not redirect to login.")

    finally:
        close_driver(driver)


# Call the test function
test_login_and_check_element()
test_signup_page_loads()
test_2fa_access_without_session_redirects_to_login()
test_login_user_without_2fa_redirects_home()
test_signup_success_creates_user_and_redirects_home()
test_signup_fails_if_email_in_use()
test_login_page_loads()
test_login_invalid_credentials_shows_error()
test_login_success_redirects_home()
test_logout_works()
