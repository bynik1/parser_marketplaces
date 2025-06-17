import logging
from datetime import datetime
import threading
import concurrent.futures
import sys
import json
from time import sleep
from typing import List
from pathlib import Path
import re
from dataclasses import dataclass, field
from typing import Optional
import os
from django.conf import settings

from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeRemainingColumn
from rich.logging import RichHandler
from curl_cffi import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)
logger.info("Приложение запущено")

@dataclass
class Product:
    name: str
    url: str
    image_url: str
    price: float
    available_quantity: int
    product_id: str
    delivery_date: str
    merchant_id: str
    merchant_name: str
    brand: Optional[str] = field(default=None)
    merchant_rating: Optional[bool] = field(default=None)
    old_price: float = field(default=0.0)
    rating: Optional[float] = field(default=None)
    reviews_count: Optional[int] = field(default=None)

    @property
    def bonus_percent(self) -> int:
        return 0

class ProductManager:
    def __init__(
        self,
        product_name: str,
        include: str = "",
        exclude: str = "",
        cookie_file_path: str = "",
        threads: int | None = None,
        delay: float | None = None,
        error_delay: float | None = None,
        log_level: str = "INFO",
        max_pages: int | None = None,
        sorting: int = 0,
        price_min: str = '',
        price_max: str = '',
    ):
        self.cookie_file_path = cookie_file_path
        self.connection_success_delay = delay or 1.8
        self.connection_error_delay = error_delay or 10.0
        self.log_level = log_level
        self.max_pages = max_pages
        self.start_time: datetime | None = None
        self.region_id = "54"
        self.cookie_dict: dict | None = None
        self.rich_progress = None
        self.logger: logging.Logger = self._create_logger(self.log_level)
        self.product_name = product_name
        self.include = include
        self.exclude = exclude
        self.threads = threads or 1
        self.sorting = sorting
        self.price_min = price_min
        self.price_max = price_max
        self.scraped_tems_counter = 0
        self.address_id = None
        self.lock = threading.Lock()
        self.parsed_offers: List[Product] = []
        self._set_up()
        self.session = self._new_session()

    def _new_session(self) -> requests.Session:
        session = requests.Session(impersonate="chrome")
        session.cookies.update(self.cookie_dict or {})
        session.cookies["adult_disclaimer_confirmed"] = "1"
        return session

    def _create_logger(self, log_level: str) -> logging.Logger:
        logging.basicConfig(
            level=log_level,
            format="%(message)s",
            datefmt="%H:%M:%S",
            handlers=[RichHandler(rich_tracebacks=True)],
        )
        return logging.getLogger("rich")

    def _set_up(self) -> None:
        self.cookie_dict = self.cookie_file_path and self.parse_cookie_file(self.cookie_file_path)
        if self.include and not self.validate_regex(self.include):
            sys.exit(f'Неверное выражение "{self.include}"!')
        if self.exclude and not self.validate_regex(self.exclude):
            sys.exit(f'Неверное выражение "{self.exclude}"!')

    def parse(self) -> None:
        self.start_time = datetime.now()
        self.logger.info("Поиск товара: %s", self.product_name)
        self.logger.info("Потоков: %s", self.threads)
        self.logger.info("Сортировка: %s", self.sorting)
        self.logger.info("Фильтры цен: price_min=%s, price_max=%s", self.price_min, self.price_max)
        self.logger.info("%s %s", self.product_name, self.start_time.strftime("%d-%m-%Y %H:%M:%S"))
        self._parse_multi_page()
        self.logger.info("Спаршено %s товаров", self.scraped_tems_counter)

    def slugify(self, text: str) -> str:
        lowercase_text = text.lower()
        slug = re.sub(r"[^\w\s-]", "_", lowercase_text).strip().replace(" ", "_")
        return slug

    def validate_regex(self, pattern: str) -> bool:
        try:
            re.compile(pattern)
        except re.error:
            return False
        return True

    def parse_cookie_file(self, path: str) -> dict:
        file_path = Path(path)
        if not file_path.exists():
            sys.exit(f"Путь {path} не найден!")
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                cookies: list = json.load(file)
                return {cookie["name"]: cookie["value"] for cookie in cookies}
        except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
            sys.exit(f"Ошибка при чтении файла кук: {e}")

    def _api_request(self, api_url: str, json_data: dict, headers: dict, tries: int = 10, delay: float = 0) -> dict:
        json_data["addressId"] = self.address_id or ""
        json_data["auth"] = {
            "locationId": self.region_id,
            "appPlatform": "WEB",
            "appVersion": 0,
            "os": "UNKNOWN_OS",
        }
        for i in range(tries):
            try:
                response = self.session.post(api_url, json=json_data, headers=headers, verify=False)
                response_data: dict = response.json()
            except Exception:
                response = None
            if response and response.status_code == 200 and not response_data.get("error"):
                return response_data
            if response and response.status_code == 200 and response_data.get("code") == 7:
                self.logger.debug("Слишком частые запросы")
                sleep(self.connection_error_delay)
            else:
                sleep(1 * i)
        sys.exit("Ошибка получения данных api")

    def _get_headers_with_referer(self, referer_url: str) -> dict:
        headers = {
            "accept": "application/json",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "cache-control": "no-cache",
            "content-type": "application/json",
            "origin": "https://megamarket.ru",
            "pragma": "no-cache",
            "priority": "u=1, i",
            "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
            "x-requested-with": "XMLHttpRequest",
        }
        if referer_url:
            headers["referer"] = referer_url
        return headers

    def _get_page(self, offset: int) -> dict:
        json_data = {
            "requestVersion": 10,
            "limit": 44,
            "offset": offset,
            "isMultiCategorySearch": False,
            "searchByOriginalQuery": False,
            "selectedSuggestParams": [],
            "expandedFiltersIds": [],
            "sorting": self.sorting,
            "ageMore18": None,
            "addressId": self.address_id,
            "showNotAvailable": True,
            "selectedFilters": [],
            "collectionId": None,
            "searchText": self.product_name,
            "selectedAssumedCollectionId": None,
            "merchant": None,
        }
        try:
            if self.price_min.strip():
                json_data["selectedFilters"].append({
                    "filterId": "88C83F68482F447C9F4E401955196697",
                    "type": 1,
                    "value": str(int(float(self.price_min)))
                })
            if self.price_max.strip():
                json_data["selectedFilters"].append({
                    "filterId": "88C83F68482F447C9F4E401955196697",
                    "type": 2,
                    "value": str(int(float(self.price_max)))
                })
            logger.info(f"Фильтры цен: selectedFilters={json_data['selectedFilters']}")
        except ValueError as e:
            logger.error(f"Ошибка при обработке цен: {e}, price_min={self.price_min}, price_max={self.price_max}")

        headers = self._get_headers_with_referer("")
        return self._api_request(
            "https://megamarket.ru/api/mobile/v1/catalogService/catalog/search",
            json_data,
            headers=headers,
            delay=self.connection_success_delay,
        )

    def _parse_page(self, response_json: dict) -> bool:
        items_per_page = int(response_json.get("limit", 44))
        if items_per_page == 0:
            return False
        page_progress = self.rich_progress.add_task(f"[orange]Страница {int(int(response_json.get('offset', 0)) / items_per_page) + 1}")
        self.rich_progress.update(page_progress, total=len(response_json["items"]))
        for item in response_json["items"]:
            if len(self.parsed_offers) >= 16:
                self.rich_progress.update(page_progress, advance=1)
                return False
            item_title = item["goods"]["title"]
            if self._exclude_check(item_title) or (item["isAvailable"] is not True) or (not self._include_check(item_title)):
                self.rich_progress.update(page_progress, advance=1)
                continue
            json_data = {
                "addressId": self.address_id or "",
                "collectionId": None,
                "goodsId": item["goods"]["goodsId"],
                "listingParams": {
                    "priorDueDate": "UNKNOWN_OFFER_DUE_DATE",
                    "selectedFilters": [],
                },
                "merchantId": "0",
                "requestVersion": 11,
                "shopInfo": {},
            }
            headers = self._get_headers_with_referer(item["goods"]["webUrl"])
            response_offers = self._api_request(
                "https://megamarket.ru/api/mobile/v1/catalogService/productOffers/get",
                json_data,
                headers=headers,
                delay=self.connection_success_delay
            )
            if response_offers.get("success") and response_offers.get("offers") and len(response_offers["offers"]) > 0:
                offer = response_offers["offers"][0]
                delivery_date = offer["deliveryPossibilities"][0].get("displayDeliveryDate", "")
                product_id = offer.get("goodsId", item["goods"]["goodsId"].split("_")[0])
                old_price = offer.get("oldPrice", 0) or offer.get("finalPrice", 0)
                parsed_offer = Product(
                    name=item["goods"]["title"],
                    url=item["goods"]["webUrl"],
                    image_url=item["goods"]["titleImage"],
                    price=offer.get("finalPrice", 0),
                    available_quantity=offer.get("availableQuantity", 0),
                    product_id=product_id,
                    delivery_date=delivery_date,
                    merchant_id=offer.get("merchantId", ""),
                    merchant_name=offer.get("merchantName", ""),
                    brand=item["goods"].get("brand", None),
                    merchant_rating=offer.get("merchantSummaryRating"),
                    old_price=old_price,
                    rating=item.get("rating", None),
                    reviews_count=item.get("reviewCount", None),
                )
                if parsed_offer.image_url:
                    ImageDownloader.save_images(parsed_offer.product_id, parsed_offer.image_url)
                with self.lock:
                    self.parsed_offers.append(parsed_offer)
                    self.scraped_tems_counter += 1
            self.rich_progress.update(page_progress, advance=1)
        self.rich_progress.remove_task(page_progress)
        return len(self.parsed_offers) < 16 and response_json["items"] and response_json["items"][-1]["isAvailable"]

    def _exclude_check(self, title: str) -> bool:
        if self.exclude:
            return bool(re.search(self.exclude, title))
        return False

    def _include_check(self, title: str) -> bool:
        if self.include:
            return bool(re.search(self.include, title))
        return True

    def _create_progress_bar(self) -> None:
        self.rich_progress = Progress(
            "{task.description}",
            SpinnerColumn(),
            BarColumn(),
            TextColumn("[progress.percentage]{task.completed}/{task.total}"),
            TimeRemainingColumn(elapsed_when_finished=True, compact=True),
        )
        self.rich_progress.start()

    def _process_page(self, offset: int, main_job) -> tuple[bool, dict]:
        response_json = self._get_page(offset)
        parse_next_page = self._parse_page(response_json)
        self.rich_progress.update(main_job, advance=1)
        return parse_next_page, response_json

    def _parse_multi_page(self) -> None:
        start_offset = 0
        item_count_total = None

        self._create_progress_bar()
        pages_to_parse = [start_offset]
        main_job = self.rich_progress.add_task("[green]Общий прогресс", total=1)

        max_threads = min(len(pages_to_parse), self.threads)
        while pages_to_parse and len(self.parsed_offers) < 16:
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
                futures = {executor.submit(self._process_page, page, main_job): page for page in pages_to_parse}
                for future in concurrent.futures.as_completed(futures):
                    try:
                        parse_next_page, response_json = future.result()
                        page = futures[future]
                        if page == start_offset and item_count_total is None:
                            items_per_page = int(response_json.get("limit", 44))
                            item_count_total = int(response_json["total"])
                            if self.max_pages is not None:
                                max_items = self.max_pages * items_per_page
                                item_count_total = min(item_count_total, max_items)
                            pages_to_parse = list(range(items_per_page, item_count_total, items_per_page))
                            self.rich_progress.update(main_job, total=len(pages_to_parse) + 1)
                        if page in pages_to_parse:
                            pages_to_parse.remove(page)
                        if parse_next_page and len(self.parsed_offers) < 16:
                            next_page = page + items_per_page
                            if next_page < item_count_total and next_page not in pages_to_parse:
                                pages_to_parse.append(next_page)
                        else:
                            self.logger.info("Дальше товары не в наличии или достигнуто 16 товаров, парсинг завершен")
                            for fut in futures:
                                future_page = futures[fut]
                                if future_page > page:
                                    if future_page in pages_to_parse:
                                        pages_to_parse.remove(future_page)
                                    self.rich_progress.update(main_job, total=len(pages_to_parse) + 1)
                                    fut.cancel()
                    except Exception:
                        continue
        self.rich_progress.stop()

    def _output_offers(self) -> None:
        output_data = [
            {
                "name": offer.name,
                "url": offer.url,
                "image_url": offer.image_url,
                "price": offer.price,
                "available_quantity": offer.available_quantity,
                "product_id": offer.product_id,
                "delivery_date": offer.delivery_date,
                "merchant_id": offer.merchant_id,
                "merchant_name": offer.merchant_name,
                "brand": offer.brand,
                "merchant_rating": offer.merchant_rating,
                "old_price": offer.old_price,
                "rating": offer.rating,
                "reviews_count": offer.reviews_count,
            }
            for offer in self.parsed_offers
        ]

        output_file = f"{self.slugify(self.product_name)}_offers.json"
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            self.logger.info(f"Спаршенные товары сохранены в {output_file}")
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении в файл: {e}")

        self.logger.info("Спаршенные товары:")
        for i, offer in enumerate(output_data):
            self.logger.info(
                f"{i}) Название: {offer['name']}, Бренд: {offer['brand'] or '-'}, "
                f"Цена: {offer['price']} руб., Старая цена: {offer['old_price']} руб., "
                f"Рейтинг: {offer['rating'] or '-'}, Количество отзывов: {offer['reviews_count'] or '-'}, "
                f"Количество: {offer['available_quantity']}, URL: {offer['url']}, "
                f"Дата доставки: {offer['delivery_date'] or '-'}"
            )
        self.logger.info(f"Всего выведено товаров: {len(output_data)}")

class ImageDownloader:
    @staticmethod
    def save_images(product_id: str, image_url: str, timeout: int = 10):
        folder_path = os.path.join(settings.MEDIA_ROOT, 'image', 'mm', str(product_id))
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

if __name__ == "__main__":
    product_name = input("Введите название товара для поиска: ")
    sorting_value = int(input("Введите значение сортировки (например, 0 для по умолчанию, 1 для по цене и т.д.): "))
    parser = ProductManager(
        product_name=product_name,
        cookie_file_path="cookies.json",
        log_level="DEBUG",
        max_pages=1,
        sorting=sorting_value,
    )
    parser.parse()