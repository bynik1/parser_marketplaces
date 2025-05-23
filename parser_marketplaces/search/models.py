from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError  # Добавляем импорт
from django.contrib.auth import get_user_model


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


class Marketplace(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Название маркетплейса"
    )
    url = models.URLField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Официальный сайт"
    )

    class Meta:
        verbose_name = "Маркетплейс"
        verbose_name_plural = "Маркетплейсы"
        ordering = ("name",)

    def __str__(self):
        return self.name
    
    
class Product(models.Model):
    marketplace = models.ForeignKey(Marketplace, on_delete=models.CASCADE, related_name='products')
    product_id = models.BigIntegerField()  # ID товара на маркетплейсе
    name = models.CharField(max_length=510)
    brand = models.CharField(max_length=100, blank=True, null=True)
    review_rating = models.FloatField(blank=True, null=True)
    feedbacks = models.IntegerField(blank=True, null=True)
    color = models.CharField(max_length=50, blank=True, null=True)
    price_product = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    price_basic = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    supplier_id = models.BigIntegerField(blank=True, null=True)
    supplier_rating = models.FloatField(blank=True, null=True)
    pics = models.IntegerField(default=0)
    first_image_path = models.CharField(max_length=1024, blank=True, null=True)
    searchquery = models.ForeignKey('SearchQuery', on_delete=models.SET_NULL, related_name='products', null=True, blank=True)
    url = models.URLField(max_length=1024, blank=True, null=True)
    delivery_date = models.CharField(max_length=255, blank=True, null=True)
    duty = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    def __str__(self):
        return f"{self.name} ({self.marketplace.name})"

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
    marketplaces = models.ManyToManyField('Marketplace', related_name='search_queries')

    def __str__(self):
        m_names = ', '.join(self.marketplaces.values_list('name', flat=True)[:3])
        return f"Запрос \"{self.query_text}\" пользователя {self.user.username} ({m_names})"
    
    @property
    def sort_label(self):
        """Return human readable label for selected sort filter."""
        return dict(SORT_VALUE_CHOICES).get(self.sort_value, self.sort_value)