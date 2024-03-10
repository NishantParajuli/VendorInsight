from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, Product, Category, Inventory, Discount


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
    # Adding inventory fields
    current_stock = forms.IntegerField(label="Current Stock")
    safety_stock_level = forms.IntegerField(label="Safety Stock Level")
    reorder_point = forms.IntegerField(label="Reorder Point")

    # Adding discount fields
    discount_type = forms.ChoiceField(
        choices=Discount.DiscountType.choices, required=False, label="Discount Type")
    discount_value = forms.DecimalField(
        label="Discount Value", max_digits=5, decimal_places=2, required=False)
    start_date = forms.DateTimeField(label="Discount Start Date", required=False, widget=forms.widgets.DateTimeInput(
        attrs={'type': 'datetime-local'}), input_formats=['%Y-%m-%dT%H:%M'])
    end_date = forms.DateTimeField(label="Discount End Date", required=False, widget=forms.widgets.DateTimeInput(
        attrs={'type': 'datetime-local'}), input_formats=['%Y-%m-%dT%H:%M'])

    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'categories']

    def __init__(self, *args, **kwargs):
        # Extract user from kwargs and remove it
        self.user = kwargs.pop('user', None)
        super(ProductForm, self).__init__(*args, **kwargs)
        self.fields['categories'].widget = forms.CheckboxSelectMultiple()
        self.fields['categories'].queryset = Category.objects.all()

    def save(self, commit=True):
        product = super().save(commit=False)
        # Set the product's user to the one passed during form initialization
        product.user = self.user

        if commit:
            # Handle inventory
            inventory = Inventory(
                current_stock=self.cleaned_data['current_stock'],
                safety_stock_level=self.cleaned_data['safety_stock_level'],
                reorder_point=self.cleaned_data['reorder_point']
            )
            inventory.save()

            # Handle discount if provided
            discount = None
            if self.cleaned_data['discount_type']:
                discount = Discount(
                    discount_type=forms.ChoiceField(
                        choices=Discount.DiscountType.choices, required=False, label="Discount Type"),
                    discount_value=self.cleaned_data['discount_value'],
                    start_date=self.cleaned_data['start_date'],
                    end_date=self.cleaned_data['end_date']
                )
                discount.save()

            product.inventory = inventory
            product.discount = discount
            product.save()

            self.save_m2m()  # Save many-to-many data for the form.
        return product
