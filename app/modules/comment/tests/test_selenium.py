import time

import pytest
from selenium.common.exceptions import NoAlertPresentException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from core.environment.host import get_host_for_selenium_testing
from core.selenium.common import close_driver, initialize_driver


# -----------------------------
# TEST 1: Añadir comentario
# -----------------------------
def test_add_comment():
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()

        driver.get(f"{host}/")
        time.sleep(2)

        driver.find_element(By.LINK_TEXT, "Login").click()
        time.sleep(1)

        email_field = driver.find_element(By.NAME, "email")
        password_field = driver.find_element(By.NAME, "password")

        email_field.send_keys("user1@example.com")
        password_field.send_keys("1234")
        password_field.send_keys(Keys.RETURN)
        time.sleep(3)

        driver.find_element(By.LINK_TEXT, "Sample dataset 4").click()
        time.sleep(2)

        comment_field = driver.find_element(By.ID, "comment-content")
        comment_field.click()
        comment_text = "Comentario de prueba"
        comment_field.send_keys(comment_text)

        driver.find_element(By.CSS_SELECTOR, ".btn-primary:nth-child(3)").click()
        time.sleep(2)

        try:
            comments_section = driver.find_element(By.ID, "comments-section")
            comments_section.find_element(By.XPATH, f".//p[contains(text(), '{comment_text}')]")
            print("Test passed! Comment added successfully.")
        except NoSuchElementException:
            raise AssertionError("Test failed! Comment was not added.")

    finally:
        close_driver(driver)


# -----------------------------
# TEST 2: Eliminar comentario
# -----------------------------


def test_delete_comment():
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()

        # ---------------------------
        # LOGIN USER1 Y CREAR COMENTARIO
        # ---------------------------
        driver.get(f"{host}/")
        time.sleep(2)

        driver.find_element(By.LINK_TEXT, "Login").click()
        time.sleep(1)

        driver.find_element(By.NAME, "email").send_keys("user1@example.com")
        driver.find_element(By.NAME, "password").send_keys("1234", Keys.RETURN)
        time.sleep(2)

        driver.find_element(By.LINK_TEXT, "Sample dataset 4").click()
        time.sleep(2)

        comment_text = "Comentario a borrar"
        driver.find_element(By.ID, "comment-content").send_keys(comment_text)

        # botón crear comentario
        driver.find_element(By.CSS_SELECTOR, ".btn-primary:nth-child(3)").click()
        time.sleep(2)

        # cerrar sesión
        driver.find_element(By.LINK_TEXT, "Log out").click()
        time.sleep(1)

        # ---------------------------
        # LOGIN USER2 Y BORRAR EL COMENTARIO
        # ---------------------------
        driver.find_element(By.LINK_TEXT, "Login").click()
        time.sleep(1)

        driver.find_element(By.NAME, "email").send_keys("user2@example.com")
        driver.find_element(By.NAME, "password").send_keys("1234", Keys.RETURN)
        time.sleep(2)

        driver.find_element(By.LINK_TEXT, "Sample dataset 4").click()
        time.sleep(2)

        # buscar el comentario creado por user1
        comments_section = driver.find_element(By.ID, "comments-section")

        created_p = comments_section.find_element(By.XPATH, f".//p[contains(text(), '{comment_text}')]")

        comment_div = created_p.find_element(By.XPATH, "./ancestor::div[contains(@id, 'comment-')]")

        comment_id = comment_div.get_attribute("id").replace("comment-", "")

        # botón borrar dentro del comentario
        delete_button = comment_div.find_element(By.CSS_SELECTOR, ".btn-danger")
        delete_button.click()
        time.sleep(1)

        # ALERT 1: confirmación
        alert = driver.switch_to.alert
        assert alert.text == "Are you sure you want to delete this comment?"
        alert.accept()
        time.sleep(1)

        # ALERT 2: eliminado correctamente
        try:
            alert2 = driver.switch_to.alert
            assert alert2.text == "Comment deleted."
            alert2.accept()
        except NoAlertPresentException:
            raise AssertionError("ERROR: faltó el alert 'Comment deleted.'")

        time.sleep(1)

        # Verificar que ya NO existe el comentario
        with pytest.raises(NoSuchElementException):
            driver.find_element(By.ID, f"comment-{comment_id}")

        print("Test passed! Comment deleted successfully.")

    finally:
        close_driver(driver)


# -----------------------------
# TEST 3: Comentarios anidados
# -----------------------------


def test_nested_comments():
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()

        driver.get(f"{host}/")
        time.sleep(2)

        driver.find_element(By.LINK_TEXT, "Login").click()
        time.sleep(1)

        email_field = driver.find_element(By.NAME, "email")
        password_field = driver.find_element(By.NAME, "password")

        email_field.send_keys("user1@example.com")
        password_field.send_keys("1234")
        password_field.send_keys(Keys.RETURN)
        time.sleep(3)

        driver.find_element(By.LINK_TEXT, "Sample dataset 4").click()
        time.sleep(2)

        parent_comment_text = "Comentario padre"
        comment_field = driver.find_element(By.ID, "comment-content")
        comment_field.send_keys(parent_comment_text)

        driver.find_element(By.CSS_SELECTOR, ".btn-primary:nth-child(3)").click()
        time.sleep(2)

        comments_section = driver.find_element(By.ID, "comments-section")
        parent_p = comments_section.find_element(By.XPATH, f".//p[contains(text(), '{parent_comment_text}')]")

        parent_div = parent_p.find_element(By.XPATH, "./ancestor::div[contains(@id, 'comment-')]")
        parent_id = parent_div.get_attribute("id").replace("comment-", "")

        reply_button = parent_div.find_element(By.CSS_SELECTOR, ".btn-secondary")
        reply_button.click()
        time.sleep(1)

        child_comment_text = "Comentario hijo"
        reply_field = driver.find_element(By.ID, "comment-content")
        reply_field.send_keys(child_comment_text)

        driver.find_element(By.CSS_SELECTOR, ".btn-primary:nth-child(3)").click()
        time.sleep(2)

        try:
            parent_div.find_element(By.XPATH, f".//p[contains(text(), '{child_comment_text}')]")
            print("Test passed! Nested comment added correctly.")
        except NoSuchElementException:
            raise AssertionError("Test failed! Child comment not found under parent comment.")

    finally:
        close_driver(driver)
