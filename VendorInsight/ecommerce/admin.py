from django.contrib import admin
from .models import Category, Product, Discount, Inventory, ProductReview, Cart, CartItem, Order, OrderDetails, Wishlist
# Register your models here.

admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Discount)
admin.site.register(Inventory)
admin.site.register(ProductReview)
admin.site.register(CartItem)
admin.site.register(Cart)
admin.site.register(Order)
admin.site.register(OrderDetails)
admin.site.register(Wishlist)


class CategoryInline(admin.TabularInline):
    model = Product.categories.through


class ProductAdmin(admin.ModelAdmin):
    inlines = [
        CategoryInline,
    ]
