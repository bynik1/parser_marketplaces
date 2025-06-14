from dataclasses import dataclass
from typing import Optional, List
import requests
import os
import logging
from urllib.parse import quote, urlencode
from bs4 import BeautifulSoup
import re
from django.conf import settings

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)
logger.info("Приложение запущено")

@dataclass
class Product:
    product_id: str
    name: Optional[str]
    brand: Optional[str]
    price: Optional[int]
    original_price: Optional[int]
    rating: Optional[float]
    reviews_count: Optional[int]
    payment_type: Optional[str]
    url: Optional[str]
    image_url: Optional[str]
    delivery_date: Optional[str]
    delivery_types: Optional[List[str]]
    duty: Optional[int]
    characteristics: Optional[dict]

    @staticmethod
    def from_html_data(soup: BeautifulSoup, base_url: str = "https://market.yandex.ru"):
        # Ссылка на изображение
        image_elem = soup.find('div', attrs={'data-zone-name': 'picture'}).find('img') if soup.find('div', attrs={'data-zone-name': 'picture'}) else None
        image_url = image_elem['src'] if image_elem and image_elem.get('src') else None
        if image_url and not image_url.startswith('http'):
            image_url = base_url + image_url

        if image_url:
            # Извлечение ID из пути URL (например, /product--.../1810127360)
            match = re.search(r'/(\d+)', image_url)
            if match:
                product_id = match.group(1)
                # source = "url_path"
                # logger.info(f"Извлечён product_id из URL пути: {product_id}")
            # else:
            #     # Попытка извлечь offerId из параметра sku
            #     match = re.search(r'sku=(\d+)', url)
            #     if match:
            #         product_id = match.group(1)
            #         source = "url_sku"
            #         logger.info(f"Извлечён product_id из URL sku: {product_id}")
            #     else:
            #         logger.warning("ID не найден в URL товара")

        # Название
        name_elem = soup.find('span', attrs={'data-auto': 'snippet-title'})
        name = name_elem.text.strip() if name_elem else None

        # Бренд (извлекаем из названия, первое слово до пробела)
        brand = name.split()[0] if name and len(name.split()) > 0 else None

        # Цена
        price_elem = soup.find('span', attrs={'data-auto': 'snippet-price-current'})
        price_text = price_elem.find('span', class_=re.compile(r'ds-text_weight_bold')).text if price_elem else None
        price = int(re.sub(r'[^\d]', '', price_text)) if price_text else None

        # Исходная цена (если есть скидка)
        original_price_elem = soup.find('div', attrs={'data-auto': 'discount-badge'})
        original_price = None
        if original_price_elem and price:
            discount_elem = original_price_elem.find('span', class_=re.compile(r'ds-text_weight_med'))
            if discount_elem:
                discount_percent = int(re.sub(r'[^\d]', '', discount_elem.text))
                original_price = int(price / (1 - discount_percent / 100))

        # Рейтинг и количество отзывов
        rating_elem = soup.find('span', attrs={'data-auto': 'reviews'})
        rating = float(rating_elem.find('span', class_=re.compile(r'ds-rating__value')).text) if rating_elem else 0
        reviews_count_text = rating_elem.find('span', class_=re.compile(r'ds-text_lineClamp')).text if rating_elem else 0
        reviews_count = int(re.sub(r'[^\d]', '', reviews_count_text)) if reviews_count_text else 0

        
        # Ссылка на товар
        url_elem = soup.find('a', attrs={'data-auto': 'snippet-link'})
        url = base_url + url_elem['href'] if url_elem and url_elem.get('href') else None
        # Магазин (тип оплаты, например, "Альфа")
        payment_type = soup.find('div', class_=re.compile(r'ds-textLine'))
        payment_name = None
        if payment_type:
            shop_span = payment_type.find('span', class_=re.compile(r'ds-text_lineClamp'))
            payment_name = shop_span.get_text(strip=True) if shop_span else None
        else:
            logger.warning("Элемент с классом 'ds-textLine' не найден, shop_name будет None")
            logger.warning(f"url = {url}")

        # logger.info(f"payment_name = {payment_name}")
        
        # Дата доставки
        delivery_date_elem = soup.find('div', attrs={'data-zone-name': 'deliveryInfo'}).find('span', class_=re.compile(r'_1yLiV')) if soup.find('div', attrs={'data-zone-name': 'deliveryInfo'}) else None
        delivery_date = delivery_date_elem.text.strip() if delivery_date_elem else None

        # Типы доставки (ПВЗ, Курьер)
        delivery_types_elems = soup.find('div', attrs={'data-zone-name': 'deliveryInfo'}).find_all('span', class_=re.compile(r'_1U2DA')) if soup.find('div', attrs={'data-zone-name': 'deliveryInfo'}) else []
        delivery_types = [elem.text.strip() for elem in delivery_types_elems] if delivery_types_elems else []

        # Пошлина
        duty_elem = soup.find('div', class_=re.compile(r'_1fiGC')).find('span', class_=re.compile(r'ds-valueLine')) if soup.find('div', class_=re.compile(r'_1fiGC')) else None
        duty_text = duty_elem.find('span', class_=re.compile(r'ds-text_weight_reg')).text if duty_elem else None
        duty = int(re.sub(r'[^\d]', '', duty_text)) if duty_text else None

        # Краткие характеристики
        characteristics_elems = soup.find_all('div', class_=re.compile(r'_2Ce4O'))
        characteristics = {}
        for elem in characteristics_elems:
            key = elem.find('span', class_=re.compile(r'ds-text_color_text-secondary')).text.strip()
            value = elem.find('span', class_=re.compile(r'ds-text_color_text-primary')).text.strip()
            characteristics[key] = value

        return Product(
            product_id=product_id,
            name=name,
            brand=brand,
            price=price,
            original_price=original_price,
            rating=rating,
            reviews_count=reviews_count,
            payment_type=payment_name,
            url=url,
            image_url=image_url,
            delivery_date=delivery_date,
            delivery_types=delivery_types,
            duty=duty,
            characteristics=characteristics
        )

    def display(self):
        text = (
            f"ID товара: {self.product_id or 'N/A'}\n"
            f"Название: {self.name or 'N/A'}\n"
            f"Бренд: {self.brand or 'N/A'}\n"
            f"Цена: {self.price or 'N/A'} ₽\n"
            f"Цена без скидки: {self.original_price or 'N/A'} ₽\n"
            f"Рейтинг: {self.rating or 0}\n"
            f"Количество отзывов: {self.reviews_count or 0}\n"
            f"Магазин: {self.payment_type or 'N/A'}\n"
            f"Ссылка на товар: {self.url or 'N/A'}\n"
            f"Ссылка на изображение: {self.image_url or 'N/A'}\n"
            f"Дата доставки: {self.delivery_date or 'N/A'}\n"
            f"Типы доставки: {', '.join(self.delivery_types) if self.delivery_types else 'N/A'}\n"
            f"Пошлина: {self.duty or 'N/A'} ₽\n"
            f"Характеристики:\n" + (
                '\n'.join(f"  {k}: {v}" for k, v in self.characteristics.items()) if self.characteristics else "  N/A"
            ) + "\n"
        )
        logger.info("product: %s", text)


class YandexMarketAPI:
    BASE_URL = "https://market.yandex.ru/search"

    def __init__(self):
        self.headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cache-Control": "max-age=0",
            "Priority": "u=0, i",
            "Referer": "https://market.yandex.ru/",
            "Sec-CH-UA": '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
        }

    def search_products(self, query: str, sort: str = "dpop") -> str:
        params = {
            "text": quote(query),
            "sort": sort,  # dpop, aprice, dprice, rating
            "lr": 65,  # Новосибирск
            "gps": "82.92043,55.030199",
            "isCpa": 1,
        }
        logger.info(f"Request URL: {self.BASE_URL}?{urlencode(params)}")
        response = requests.get(self.BASE_URL, headers=self.headers, params=params)
        logger.info("HTTP Status Code: %s", response.status_code)
        with open("output.html", "w", encoding="utf-8") as file:
            file.write(response.text)
        return response.text

class ProductManager:
    def __init__(self):
        self.api = YandexMarketAPI()

    def search_and_display(self, search_query: str, search_sort: str = "dpop", save_image_all: bool = True) -> List[Product]:
        html_content = self.api.search_products(search_query, search_sort)
        # logger.info("Sample Yandex results (first 3): %s", html_content)
        products = self._parse_response(html_content)
        if not products:
            print("Товары не найдены.")
            return []

        for product in products:
            # product.display()
            if product.image_url and save_image_all:
                ImageDownloader.save_images(product.product_id, product.image_url)
        print(f"Количество товаров: {len(products)}")
        return products

    def _parse_response(self, html_content: str) -> List[Product]:
        soup = BeautifulSoup(html_content, 'html.parser')
        products = []

        # Находим все элементы товаров
        product_elements = soup.find_all('article', attrs={'data-auto': 'searchOrganic'})
        for elem in product_elements:
            product = Product.from_html_data(elem)
            if product.product_id or product.name:  # Фильтруем пустые результаты
                products.append(product)
        
        return products

class ImageDownloader:
    @staticmethod
    def save_images(product_id: str, image_url: str, timeout: int = 10):
        folder_path = os.path.join(settings.MEDIA_ROOT, 'image', 'yma', str(product_id))
        image_path = os.path.join(folder_path, "1.jpg")
        logger.info(f"Попытка загрузки изображения: {image_url}")
        try:
            response = requests.get(image_url, timeout=timeout)
            response.raise_for_status()
            os.makedirs(folder_path, exist_ok=True)
            with open(image_path, "wb") as file:
                file.write(response.content)
            logger.info(f"Успешно сохранено: {image_path}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка загрузки {image_url}: {e}")
        except OSError as e:
            logger.error(f"Ошибка сохранения файла {image_path}: {e}")

if __name__ == '__main__':
    manager = ProductManager()
    search_query = input("Введите название товара для поиска: ")
    manager.search_and_display(search_query)