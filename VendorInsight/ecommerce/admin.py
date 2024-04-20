from django.contrib import admin
from .models import User, Category, Product, Discount, Inventory, ProductReview, Cart, CartItem, Order, OrderDetails, Wishlist, UserProfile, UserInteraction
# Register your models here.

admin.site.register(User)
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
admin.site.register(UserProfile)
admin.site.register(UserInteraction)


class CategoryInline(admin.TabularInline):
    model = Product.categories.through


class ProductAdmin(admin.ModelAdmin):
    inlines = [
        CategoryInline,
    ]
