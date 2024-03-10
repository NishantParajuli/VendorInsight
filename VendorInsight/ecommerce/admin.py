from django.contrib import admin
from .models import Category, Product, Discount, Inventory
# Register your models here.

admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Discount)
admin.site.register(Inventory)


class CategoryInline(admin.TabularInline):
    model = Product.categories.through


class ProductAdmin(admin.ModelAdmin):
    inlines = [
        CategoryInline,
    ]
