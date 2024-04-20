from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractUser
# Create your models here.


class User(AbstractUser):
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.username


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_vendor = models.BooleanField(default=False)
    gender = models.CharField(max_length=1, choices=[(
        'M', 'Male'), ('F', 'Female'), ('O', 'Other')])
    date_of_birth = models.DateField()

    def __str__(self):
        return self.user.username


class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    inventory = models.ForeignKey('Inventory', on_delete=models.CASCADE)
    discount = models.ForeignKey(
        'Discount', on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE, related_name='products')
    categories = models.ManyToManyField('Category', related_name='products')
    total_views = models.PositiveIntegerField(default=0)

    def average_sentiment(self):
        sentiments = {'sadness': -2, 'anger': -1, 'fear': -1,
                      'joy': 2, 'love': 3, 'surprise': 1, 'neutral': 0}
        reviews = self.productreview_set.all()
        if not reviews:
            return 0
        sentiment_score = sum(sentiments.get(review.sentiment, 0)
                              for review in reviews) / len(reviews)
        return sentiment_score

    def __str__(self):
        return self.name


class ProductImage(models.Model):
    image = models.ImageField(upload_to='product_images/')
    description = models.TextField(blank=True)
    upload_date = models.DateTimeField(auto_now_add=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    def __str__(self):
        return self.image_url


class Inventory(models.Model):
    current_stock = models.PositiveIntegerField()
    safety_stock_level = models.PositiveIntegerField()
    reorder_point = models.PositiveIntegerField()


class Discount(models.Model):
    class DiscountType(models.TextChoices):
        PERCENTAGE = 'Percentage', _('Percentage')
        FIXED = 'Fixed', _('Fixed Value')

    discount_type = models.CharField(
        max_length=100,
        choices=DiscountType.choices,
        default=DiscountType.FIXED
    )
    discount_value = models.DecimalField(max_digits=5, decimal_places=2)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()


class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.name


class ProductReview(models.Model):
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    review_date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    sentiment = models.CharField(max_length=20, blank=True, null=True)


class Order(models.Model):
    order_date = models.DateTimeField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.order_date}'


class OrderDetails(models.Model):
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)


class Wishlist(models.Model):
    date_added = models.DateTimeField(auto_now_add=True)
    products = models.ManyToManyField(Product, related_name='wishlists')
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)


class Cart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)


class UserInteraction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    interaction_type = models.CharField(max_length=20, choices=[(
        'view', 'View'), ('purchase', 'Purchase'), ('wishlist', 'Wishlist')])
    timestamp = models.DateTimeField(auto_now_add=True)
