import os
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait

from core.environment.host import get_host_for_selenium_testing
from core.selenium.common import close_driver, initialize_driver


def wait_for_page_to_load(driver, timeout=4):
    WebDriverWait(driver, timeout).until(
        lambda driver: driver.execute_script("return document.readyState") == "complete"
    )


def count_datasets(driver, host):
    driver.get(f"{host}/dataset/list")
    wait_for_page_to_load(driver)

    try:
        amount_datasets = len(driver.find_elements(By.XPATH, "//table//tbody//tr"))
    except Exception:
        amount_datasets = 0
    return amount_datasets


def test_upload_csv_dataset():
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()

        # Login
        driver.get(f"{host}/login")
        wait_for_page_to_load(driver)

        email_field = driver.find_element(By.NAME, "email")
        password_field = driver.find_element(By.NAME, "password")
        email_field.send_keys("user1@example.com")
        password_field.send_keys("1234")
        password_field.send_keys(Keys.RETURN)

        time.sleep(3)
        wait_for_page_to_load(driver)

        # Count initial datasets
        initial_datasets = count_datasets(driver, host)

        # Open upload dataset page
        driver.get(f"{host}/dataset/upload")
        wait_for_page_to_load(driver)

        # Fill basic info
        driver.find_element(By.NAME, "title").send_keys("CSV Dataset Test")
        driver.find_element(By.NAME, "desc").send_keys("Testing CSV dataset upload")
        driver.find_element(By.NAME, "tags").send_keys("csv,test")

        # Add authors
        add_author_button = driver.find_element(By.ID, "add_author")
        add_author_button.click()
        wait_for_page_to_load(driver)

        driver.find_element(By.NAME, "authors-0-name").send_keys("Author0")
        driver.find_element(By.NAME, "authors-0-affiliation").send_keys("Club0")
        driver.find_element(By.NAME, "authors-0-orcid").send_keys("0000-0000-0000-0000")

        # Ruta absoluta de un CSV de prueba
        file1_path = os.path.abspath("app/modules/dataset/csv_examples/file1.csv")
        file2_path = os.path.abspath("app/modules/dataset/csv_examples/file2.csv")

        assert os.path.exists(file1_path), f"CSV file not found: {file1_path}"
        assert os.path.exists(file2_path), f"CSV file not found: {file2_path}"

        # Subir archivos CSV
        dropzone = driver.find_element(By.CLASS_NAME, "dz-hidden-input")
        dropzone.send_keys(file1_path)
        wait_for_page_to_load(driver)

        dropzone = driver.find_element(By.CLASS_NAME, "dz-hidden-input")
        dropzone.send_keys(file2_path)
        wait_for_page_to_load(driver)

        # Aceptar condiciones y enviar
        driver.find_element(By.ID, "agreeCheckbox").click()
        wait_for_page_to_load(driver)

        upload_btn = driver.find_element(By.ID, "upload_button")
        upload_btn.click()

        # Esperar a la redirección
        WebDriverWait(driver, 10).until(
            lambda d: d.current_url.endswith("/dataset/list")
        )

        # Validar que se redirige a la lista
        assert driver.current_url == f"{host}/dataset/list", "Test failed!"

        # Validar que hay un dataset más
        final_datasets = count_datasets(driver, host)
        assert final_datasets == initial_datasets + 1, "Test failed!"

        print("Test passed!")

    finally:
        close_driver(driver)


# Call the test function
test_upload_csv_dataset()
