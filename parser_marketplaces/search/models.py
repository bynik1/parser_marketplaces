from django.db import models

# Create your models here.

class ProductOzon(models.Model):
    product_id = models.BigIntegerField(unique=True, help_text="Unique product identifier")
    name = models.CharField(max_length=255)
    brand = models.CharField(max_length=100, blank=True, null=True)
    review_rating = models.FloatField(blank=True, null=True, help_text="Product rating")
    feedbacks = models.IntegerField(blank=True, null=True, help_text="Number of reviews")
    color = models.CharField(max_length=50, blank=True, null=True)
    price_product = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    price_basic = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    supplier_id = models.BigIntegerField(blank=True, null=True)
    supplier_rating = models.FloatField(blank=True, null=True)
    pics = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.name} (ID: {self.product_id})"

class Product_WB(models.Model):
    product_id = models.BigIntegerField(unique=True) # ID товара, уникальный
    name = models.CharField(max_length=255)
    brand = models.CharField(max_length=100, blank=True, null=True)
    review_rating = models.FloatField(blank=True, null=True) # рейтинг товара
    feedbacks = models.IntegerField(blank=True, null=True) # количество отзывов
    color = models.CharField(max_length=50, blank=True, null=True)
    price_product = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    price_basic = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    supplier_id = models.BigIntegerField(blank=True, null=True)
    supplier_rating = models.FloatField(blank=True, null=True)
    pics = models.IntegerField(default=0)
    first_image_path = models.CharField(max_length=510, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} (ID: {self.product_id})"