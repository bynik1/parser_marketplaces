from django.contrib import admin
from .models import SearchQuery, Product

@admin.register(Product)
class AdminSearchProduct(admin.ModelAdmin):
    list_display = ('name', 'price_product', 'feedbacks', "review_rating")

admin.site.register(SearchQuery)
# admin.site.register(Product, AdminSearchProduct)
