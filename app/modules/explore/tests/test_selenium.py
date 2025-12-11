from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from core.environment.host import get_host_for_selenium_testing
from core.selenium.common import close_driver, initialize_driver


class TestExplore:

    def setup_method(self, method):
        self.driver = initialize_driver()
        self.wait = WebDriverWait(self.driver, 10)
        self.vars = {}

    def teardown_method(self, method):
        close_driver(self.driver)

    def wait_for_results(self):
        """Espera a que aparezcan elementos dentro de #results."""
        return self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#results > div")))

    def test_explore_filters(self):
        driver = self.driver
        host = get_host_for_selenium_testing()

        driver.get(f"{host}/explore")
        driver.maximize_window()

        # ----------- BUSCAR POR TITULO-----------
        search_input = driver.find_element(By.ID, "query")
        search_input.send_keys("Sample dataset 1")
        search_input.clear()

        items_after_search = self.wait_for_results()
        assert len(items_after_search) > 0

        # MAS FILTROS
        driver.find_element(By.ID, "show-more-filters").click()

        # DESCRIPTION

        desc_input = driver.find_element(By.ID, "filter_description")
        desc_input.send_keys("Description for dataset 4")

        assert len(self.wait_for_results()) > 0
        desc_input.clear()

        # AUTHORS

        authors_input = driver.find_element(By.ID, "filter_authors")
        authors_input.send_keys("Author 1")

        assert len(self.wait_for_results()) > 0
        authors_input.clear()

        # AFFILIATION

        affiliation_input = driver.find_element(By.ID, "filter_affiliation")
        affiliation_input.send_keys("Affiliation 2")

        assert len(self.wait_for_results()) > 0
        affiliation_input.clear()

        # ORCID

        orcid_input = driver.find_element(By.ID, "filter_orcid")
        orcid_input.send_keys("0000-0001")

        assert len(self.wait_for_results()) > 0
        orcid_input.clear()

        # CSV FILENAME

        filename_input = driver.find_element(By.ID, "filter_csv_filename")
        filename_input.send_keys("file3.csv")

        assert len(self.wait_for_results()) > 0
        filename_input.clear()

        # CSV TITLE

        title_input = driver.find_element(By.ID, "filter_csv_title")
        title_input.send_keys("csv Model 2")

        assert len(self.wait_for_results()) > 0
        title_input.clear()

        # PUBLICATION DOI

        doi_input = driver.find_element(By.ID, "filter_publication_doi")
        doi_input.send_keys("10.1234/dataset1")

        assert len(self.wait_for_results()) > 0
        doi_input.clear()

        # TAGS (1 SOLA TAG)

        tags_input = driver.find_element(By.ID, "filter_tags")
        tags_input.send_keys("tag1")

        assert len(self.wait_for_results()) > 0
        tags_input.clear()

        # TAGS (2 TAGS)

        tags_input.send_keys("tag1, tag2")

        assert len(self.wait_for_results()) > 0
        tags_input.clear()

        # CLEAR FILTERS

        clear_btn = driver.find_element(By.ID, "clear-filters")
        clear_btn.click()

        assert len(self.wait_for_results()) > 0

        # SORTING
        oldest_radio = driver.find_element(By.CSS_SELECTOR, "input[type='radio'][value='oldest']")
        oldest_radio.click()

        assert len(self.wait_for_results()) > 0
