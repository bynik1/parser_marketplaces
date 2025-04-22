import time
import json
from selenium import webdriver
from selenium_stealth import stealth
from selenium_authenticated_proxy import SeleniumAuthenticatedProxy
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

# Настройка опций Chrome
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("start-maximized")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)

# Инициализация драйвера
driver = webdriver.Chrome(options=chrome_options)

# Применение Selenium Stealth
stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True)

# Переход на сайт Ozon
driver.get("https://www.ozon.ru/")
time.sleep(5)  # Ожидание загрузки страницы

element_search = driver.find_element(By.CSS_SELECTOR, "input[placeholder='Искать на Ozon']")
element_search.click()
element_search.send_keys("s24")
element_search_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
element_search_button.click()
scroll_pause = 1  # задержка между скроллами
last_height = driver.execute_script("return document.body.scrollHeight")
count_link = 0

for j in range(2):
    for i in range(3):
        # Прокрутка в самый низ
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause)

        # Получаем новую высоту документа после прокрутки
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break  # если высота не изменилась — дошли до конца
        last_height = new_height

    element_products = driver.find_elements(By.CSS_SELECTOR, "div[data-widget='tileGridDesktop']")
    for element in element_products:
        #print(element.text)  # выводит текст внутри элемента

        html = element.get_attribute("innerHTML")
        soup = BeautifulSoup(html, "html.parser")

        # print(html)
        with open("output.txt", "w", encoding="utf-8") as file:
           file.write(soup.prettify())

    #     time.sleep(5)  # Ожидание загрузки страницы
        for element in soup.find_all("div", attrs={"data-index": True}):
            print(f"Товар номер {count_link}: ")
            a_tag = element.select_one("a.tile-clickable-element")
            link = "https://www.ozon.ru" + a_tag["href"] if a_tag else None
            print(link)
            # Цена со скидкой
            price = element.select_one("span.tsHeadline500Medium")
            price = price.get_text(strip=True) if price else None
            print(price)
            # Старая цена
            old_price = element.select_one("span.tsBodyControl400Small.c390-b")
            old_price = old_price.get_text(strip=True) if old_price else None
            print(old_price)

            # Скидка
            discount = element.select_one("span.tsBodyControl400Small:not(.c390-b)")
            discount = discount.get_text(strip=True) if discount else None
            print(discount)

            # Осталось товара
            left = element.select_one("div.p6b20-a span.p6b20-a4")
            left = left.get_text(strip=True) if left else None
            print(left)

            # Название
            name = element.select_one("a.tile-clickable-element span.tsBody500Medium")
            name = name.get_text(strip=True) if name else None
            print(name)

            # Рейтинг
            rating = element.select_one("div.tsBodyMBold span:nth-of-type(1) span")
            rating = rating.get_text(strip=True) if rating else None
            print(rating)

            # Отзывы
            reviews = element.select_one("div.tsBodyMBold span:nth-of-type(2) span")
            reviews = reviews.get_text(strip=True) if reviews else None
            print(reviews)

            count_link+=1
        
page_source = driver.page_source
soup = BeautifulSoup(page_source, "html.parser")

with open("page.html", "w", encoding="utf-8") as file:
    file.write(soup.prettify())


print(f"Количество ссылок: {count_link}")
# Закрытие браузера
driver.quit()


    