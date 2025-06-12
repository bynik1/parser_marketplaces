from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.contrib.auth import get_user_model
import json

SORT_VALUE_CHOICES = [
    ("popular", "По популярности"),
    ("rate", "По рейтингу"),
    ("priceup", "По возрастанию цены"),
    ("pricedown", "По убыванию цены"),
]

# Соответствие общих значений сортировки конкретным параметрам
# каждого маркетплейса. Используется при формировании запросов к API
# маркетплейсов.
SORT_PARAM_MAPPING = {
    "popular": {"wb": "popular", "yandex": "dpop"},
    "rate": {"wb": "rate", "yandex": "rating"},
    "priceup": {"wb": "priceup", "yandex": "aprice"},
    "pricedown": {"wb": "pricedown", "yandex": "dprice"},
}

class Product(models.Model):
    marketplace_name = models.CharField(max_length=100, verbose_name="Название маркетплейса")
    product_id = models.BigIntegerField(verbose_name='Id товара')  # ID товара на маркетплейсе
    name = models.CharField(max_length=510, verbose_name='Названия')
    brand = models.CharField(max_length=100, blank=True, null=True, verbose_name='Бренд')
    review_rating = models.FloatField(blank=True, null=True, verbose_name='Рейтинг')
    feedbacks = models.IntegerField(blank=True, null=True, verbose_name='Количество отзывов')
    color = models.CharField(max_length=50, blank=True, null=True, verbose_name='Цвет')
    price_product = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name='Цена')
    price_basic = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name='Цена до скидки')
    supplier_id = models.BigIntegerField(blank=True, null=True, verbose_name='ID продавца')
    supplier_rating = models.FloatField(blank=True, null=True, verbose_name='Рейтинг продавца')
    pics = models.IntegerField(default=0, verbose_name='Количество фотографий')
    first_image_path = models.CharField(max_length=1024, blank=True, null=True, verbose_name='Путь до 1 изображения')
    searchquery = models.ForeignKey('SearchQuery', on_delete=models.SET_NULL, related_name='products', null=True, blank=True)
    url = models.URLField(max_length=1024, blank=True, null=True, verbose_name='Ссылка на товар')
    delivery_date = models.CharField(max_length=255, blank=True, null=True, verbose_name='Дата доставки')
    duty = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name='Пошлина')

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"

    def __str__(self):
        return f"{self.name} ({self.marketplace_name})"

class SearchQuery(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='search_queries')
    query_text = models.CharField(max_length=255, verbose_name="Текст запроса")
    sort_value = models.CharField(
        max_length=20,
        choices=SORT_VALUE_CHOICES,
        default="priceup",
        verbose_name="Фильтр сортировки",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    marketplace_names = models.TextField(verbose_name="Названия маркетплейсов", blank=True, default="[]")

    def get_marketplace_names(self):
        """Return list of marketplace names."""
        return json.loads(self.marketplace_names)

    def set_marketplace_names(self, names):
        """Set list of marketplace names."""
        self.marketplace_names = json.dumps(names)

    def __str__(self):
        m_names = ', '.join(json.loads(self.marketplace_names)[:3])
        return f"Запрос \"{self.query_text}\" пользователя {self.user.username} ({m_names})"
    
    @property
    def sort_label(self):
        """Return human readable label for selected sort filter."""
        return dict(SORT_VALUE_CHOICES).get(self.sort_value, self.sort_value)
    
    class Meta:
        verbose_name = "История поиска"
        verbose_name_plural = "История поиска"