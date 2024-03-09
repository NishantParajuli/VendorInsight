from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
# Create your models here.


class User(models.Model):
    username = models.CharField(max_length=30, unique=True)
    email = models.EmailField(max_length=100, unique=True)
    password = models.CharField(max_length=30)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    phone_number = models.CharField(max_length=15)
    address = models.CharField(max_length=100)
    date_joined = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username
