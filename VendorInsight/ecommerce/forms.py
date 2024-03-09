from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    phone_number = forms.CharField(max_length=15)
    address = forms.CharField(max_length=100)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2',
                  'first_name', 'last_name', 'phone_number', 'address']
