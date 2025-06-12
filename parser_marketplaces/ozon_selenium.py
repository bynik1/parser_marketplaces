import time
import json
from selenium import webdriver
from selenium_stealth import stealth
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import tempfile

class OzonParser:
    def __init__(self, query, scroll_count=2, scroll_loops=3):
        self.query = query
        self.scroll_count = scroll_count
        self.scroll_loops = scroll_loops
        self.count_link = 0
        self.driver = self._init_driver()

    def _init_driver(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless=new")  # обязательно в Linux
        chrome_options.add_argument("--no-sandbox")  # нужно в контейнере
        chrome_options.add_argument("--disable-dev-shm-usage")  # избежание /dev/shm переполнения
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("start-maximized")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")

        driver = webdriver.Chrome(options=chrome_options)

        stealth(driver,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True)

        return driver

    def open_site(self, url="https://www.ozon.ru/"):
        self.driver.get(url)

        # Ожидаем появления строки поиска (как индикатор загрузки)
        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='Искать на Ozon']"))
            )
        except Exception as e:
            print(f"Ошибка при загрузке страницы: {e}")
            self.driver.save_screenshot("/app/ozon_error.png")


    def search_product(self):
        element_search = self.driver.find_element(By.CSS_SELECTOR, "input[placeholder='Искать на Ozon']")
        element_search.click()
        element_search.send_keys(self.query)
        element_search_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        element_search_button.click()

    def scroll_and_parse(self):
        last_height = self.driver.execute_script("return document.body.scrollHeight")

        for j in range(self.scroll_count):
            for i in range(self.scroll_loops):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            self._parse_products()

    def _parse_products(self):
        elements = self.driver.find_elements(By.CSS_SELECTOR, "div[data-widget='tileGridDesktop']")
        for element in elements:
            html = element.get_attribute("innerHTML")
            soup = BeautifulSoup(html, "html.parser")

            for product in soup.find_all("div", attrs={"data-index": True}):
                self._print_product_info(product)

    def _print_product_info(self, element):
        print(f"Товар номер {self.count_link}: ")

        def get_text(selector, cls=None):
            el = element.select_one(selector if not cls else f"{selector}.{cls}")
            return el.get_text(strip=True) if el else None

        def get_attr(selector, attr):
            el = element.select_one(selector)
            return el[attr] if el and attr in el.attrs else None

        link = get_attr("a.tile-clickable-element", "href")
        print(f"https://www.ozon.ru{link}" if link else None)

        print(get_text("span", "tsHeadline500Medium"))  # price
        print(get_text("span", "tsBodyControl400Small.c390-b"))  # old price
        print(get_text("span.tsBodyControl400Small:not(.c390-b)"))  # discount
        print(get_text("div.p6b20-a span.p6b20-a4"))  # left
        print(get_text("a.tile-clickable-element span.tsBody500Medium"))  # name
        print(get_text("div.tsBodyMBold span:nth-of-type(1) span"))  # rating
        print(get_text("div.tsBodyMBold span:nth-of-type(2) span"))  # reviews

        self.count_link += 1

    def save_full_page(self, filename="page.html"):
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        with open(filename, "w", encoding="utf-8") as file:
            file.write(soup.prettify())

    def run(self):
        self.open_site()
        self.search_product()
        self.scroll_and_parse()
        self.save_full_page()
        print(f"Количество ссылок: {self.count_link}")
        self.driver.quit()


if __name__ == "__main__":
    query = input("Напишите товар для поиска: ")
    while not query:
        query = input("Напишите, пожалуйста товар для поиска: ")
    parser = OzonParser(query="s24")
    parser.run()
