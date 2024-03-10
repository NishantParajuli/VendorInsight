from django.shortcuts import render,  redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from .forms import UserRegisterForm, ProductForm
from django.contrib import messages
from .models import UserProfile
from django.http import HttpResponseForbidden


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            messages.success(request, f'Account created for {username}!')
            if form.cleaned_data['is_vendor']:
                # Redirect to a vendor-specific page if registered as a vendor
                return redirect('vendor_home')
            else:
                # Redirect to the regular home page
                return redirect('home')
    else:
        form = UserRegisterForm()
    return render(request, 'ecommerce/register.html', {'form': form})


def vendor_required(func):
    def check_vendor(request, *args, **kwargs):
        try:
            user_profile = request.user.userprofile
            if user_profile.is_vendor:
                return func(request, *args, **kwargs)
            else:
                return HttpResponseForbidden()
        except UserProfile.DoesNotExist:
            return HttpResponseForbidden()
    return check_vendor


@login_required  # This is a decorator that will redirect to the login page if the user is not logged in
def home(request):
    return render(request, 'ecommerce/home.html')


@login_required
@vendor_required
def vendor_home(request):
    # Your vendor-specific view logic
    return render(request, 'ecommerce/vendor_page.html')


@login_required
@vendor_required
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product added successfully!')
            return redirect('vendor_home')
    else:
        form = ProductForm(user=request.user)
    return render(request, 'ecommerce/add_product.html', {'form': form})
