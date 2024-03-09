from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, Product, Category, Inventory, Vendor


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    phone_number = forms.CharField(max_length=15)
    address = forms.CharField(max_length=100)
    is_vendor = forms.BooleanField(required=False, label='Register as vendor')

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2',
                  'first_name', 'last_name', 'phone_number', 'address', 'is_vendor']

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            user_profile = UserProfile(
                user=user, is_vendor=self.cleaned_data['is_vendor'])
            user_profile.save()
        return user


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price',
                  'inventory', 'discount', 'categories']

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(ProductForm, self).__init__(*args, **kwargs)
        self.fields['categories'].widget = forms.CheckboxSelectMultiple()
        self.fields['categories'].queryset = Category.objects.all()

    def save(self, commit=True):
        product = super().save(commit=False)
        if commit:
            product.save()
            self.save_m2m()  # Save many-to-many data for the form.
        return product
