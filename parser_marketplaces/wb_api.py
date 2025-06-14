from dataclasses import dataclass
from typing import Optional
from django.conf import settings
import requests
import os
import time
import logging
import json
from urllib.parse import urlencode
from datetime import datetime, timedelta
import math

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)
logger.info("Приложение запущено внутри контейнера")


@dataclass
class Product:
    product_id: int
    name: str
    brand: str
    review_rating: Optional[float]
    feedbacks: Optional[int]
    color: Optional[str]
    price_product: Optional[int]
    price_basic: Optional[int]
    supplier_id: Optional[int]
    supplier_rating: Optional[float]
    pics: int
    first_image_path: Optional[str] = None
    delivery_date: Optional[str] = None  # New field for delivery date


    @staticmethod
    def from_api_data(data):
        image_path = f"image/{data.get('id')}/1.jpg" if data.get('pics') > 0 else None
        
        # Calculate delivery date
        delivery_date = None
        time2 = data.get('time2')
        logger.info(f"time2 = {time2}")
        if time2 is not None:
            days = math.ceil(time2 / 24)  # Divide by 24 and round up
            current_date = datetime.now()
            delivery = current_date + timedelta(days=days)
            # Format as "date month_name" (e.g., "15 June")
            month_names = [
                "Января", "Февраля", "Марта", "Апреля", "Мая", "Июня",
                "Июля", "Августа", "Сентября", "Октября", "Ноября", "Декабря"
            ]
            delivery_date = f"{delivery.day} {month_names[delivery.month - 1]}"

        return Product(
            product_id=data.get('id'),
            name=data.get('name'),
            brand=data.get('brand'),
            review_rating=data.get('reviewRating'),
            feedbacks=data.get('feedbacks'),
            color=Product._get_color(data),
            price_product=Product._get_price(data, 'product'),
            price_basic=Product._get_price(data, 'basic'),
            supplier_id=data.get('supplierId'),
            supplier_rating=data.get('supplierRating'),
            pics=data.get('pics', 0),
            first_image_path=image_path,
            delivery_date=delivery_date
        )


    @staticmethod
    def _get_color(data):
        if 'colors' in data and len(data['colors']) > 0:
            return data['colors'][0].get('name')
        return None


    @staticmethod
    def _get_price(data, price_type):
        if 'sizes' in data and len(data['sizes']) > 0:
            price_raw = data['sizes'][0].get('price', {}).get(price_type)
            if price_raw is not None:
                return int(price_raw / 100)
        return None


    def display(self):
        text = (
            f"Название: {self.name}\n"
            f"Цвет: {self.color}\n"
            f"Бренд: {self.brand}\n"
            f"Цена без скидки: {self.price_basic}\n"
            f"Цена со скидкой: {self.price_product}\n"
            f"Отзывов всего: {self.feedbacks}\n"
            f"Средняя оценка: {self.review_rating}\n"
            f"Ссылка на товар: https://www.wildberries.ru/catalog/{self.product_id}/detail.aspx\n"
            f"Ссылка на продавца: https://www.wildberries.ru/seller/{self.supplier_id}\n"
            f"Средняя оценка продавца: {self.supplier_rating}\n"
            f"Количество фоток: {self.pics}\n"
            f"Путь к 1 изображению: {self.first_image_path}\n"
            f"Дата доставки: {self.delivery_date}\n"  # Added delivery date to display
        )
        logger.info(text)


class WildberriesAPI:
    BASE_URL = 'https://search.wb.ru/exactmatch/ru/male/v13/search'

    def __init__(self):
        self.headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "origin": "https://www.wildberries.ru",
            "priority": "u=1, i",
            "referer": "https://www.wildberries.ru/",
            "sec-ch-ua": "\"Google Chrome\";v=\"135\", \"Not-A.Brand\";v=\"8\", \"Chromium\";v=\"135\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
        }


    def search_products(self, query, sort):
        self.to_url_safe_format(query)
        params = {
            'ab_old_spell': 'spell',
            'appType': '1',
            'curr': 'rub',
            'dest': '-364776',
            'hide_dtype': '13',
            'lang': 'ru',
            'page': '1',
            'query': query,
            'resultset': 'catalog',
            'sort': sort,
            'spp': '30',
            'suppressSpellcheck': 'false',
            'uclusters': '3',
            'uiv': '0'
        }
        logger.info(f"Request URL: {self.BASE_URL}?{urlencode(params)}")
        response = requests.get(self.BASE_URL, headers=self.headers, params=params)
        try:
            return response.json()
        except ValueError:
            logger.error("Invalid JSON response")
            return {}


    @staticmethod
    def to_url_safe_format(query):
        encoded_query_url = []
        for char in query:
            if ('a' <= char <= 'z' or 'A' <= char <= 'Z' or '0' <= char <= '9'):
                encoded_query_url.append(char)
            else:
                char_encoded = ''.join(f'%{byte:02X}' for byte in char.encode('utf-8'))
                encoded_query_url.append(char_encoded)
        return encoded_query_url


class ProductManager:
    def __init__(self):
        self.api = WildberriesAPI()

    def search_and_display(self, search_query: str, search_sort='popular', save_image_all=False):
        response = self.api.search_products(search_query, search_sort)
        products = self._parse_response(response)[:16]
        if not products:
            logger.info("Товары не найдены.")
            return
        for product in products:
            # product.display()  # Display product details including delivery date
            if product.pics > 0:
                ImageDownloader.save_images(product.product_id, product.pics, save_image_all)
        logger.info(f"Количество товаров: {len(products)}")
        return products

    def _parse_response(self, response):
        products_raw = response.get('data', {}).get('products', [])
        return [Product.from_api_data(data) for data in products_raw]


class ImageDownloader:
    @staticmethod
    def save_images(product_id, product_pics, save_image_all, timeout=10):
        _short_id = product_id // 100000
        folder_path = os.path.join(settings.MEDIA_ROOT, 'image', 'wb', str(product_id))
        os.makedirs(folder_path, exist_ok=True)
        basket = ImageDownloader._determine_basket(_short_id)
        if not save_image_all:
            product_pics = 1
        for i in range(1, product_pics + 1):
            image_url = f"https://basket-{basket}.wbbasket.ru/vol{_short_id}/part{product_id // 1000}/{product_id}/images/big/{i}.webp"
            image_path = f"{folder_path}/{i}.jpg"
            logger.info(f"Попытка загрузки изображения: {image_url}")
            try:
                response = requests.get(image_url)
                response.raise_for_status()
                with open(image_path, "wb") as file:
                    file.write(response.content)
                logger.info(f"Успешно сохранено: {image_path}")
            except requests.exceptions.RequestException as e:
                logger.error(f"Ошибка загрузки {image_url}: {e}")
            except requests.exceptions.HTTPError as err:
                logger.error(f"Сервер вернул ошибку: {err.response.status_code}")
            except requests.exceptions.ConnectionError:
                logger.error("Не удалось подключиться к серверу")
            except requests.exceptions.Timeout:
                logger.error("Превышено время ожидания")


    @staticmethod
    def _determine_basket(_short_id):
        if 0 <= _short_id <= 143:
            return '01'
        elif 144 <= _short_id <= 287:
            return '02'
        elif 288 <= _short_id <= 431:
            return '03'
        elif 432 <= _short_id <= 719:
            return '04'
        elif 720 <= _short_id <= 1007:
            return '05'
        elif 1008 <= _short_id <= 1061:
            return '06'
        elif 1062 <= _short_id <= 1115:
            return '07'
        elif 1116 <= _short_id <= 1169:
            return '08'
        elif 1170 <= _short_id <= 1313:
            return '09'
        elif 1314 <= _short_id <= 1601:
            return '10'
        elif 1602 <= _short_id <= 1655:
            return '11'
        elif 1656 <= _short_id <= 1919:
            return '12'
        elif 1920 <= _short_id <= 2045:
            return '13'
        elif 2046 <= _short_id <= 2189:
            return '14'
        elif 2190 <= _short_id <= 2405:
            return '15'
        elif 2406 <= _short_id <= 2621:
            return '16'
        elif 2622 <= _short_id <= 2836:
            return '17'
        elif 2837 <= _short_id <= 3053:
            return '18'
        elif 3054 <= _short_id <= 3269:
            return '19'
        elif 3270 <= _short_id <= 3485:
            return '20'
        elif 3486 <= _short_id <= 3701:
            return '21'
        elif 3702 <= _short_id <= 3917:
            return '22'
        elif 3918 <= _short_id <= 4133:
            return '23'
        elif 4134 <= _short_id <= 4349:
            return '24'
        elif 4350 <= _short_id <= 4565:
            return '25'
        elif 4566 <= _short_id <= 4781:
            return '26'
        else:
            return '27'


if __name__ == '__main__':
    manager = ProductManager()
    search_query = input("Введите название товара для поиска: ")
    manager.search_and_display(search_query)