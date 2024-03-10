from django.shortcuts import render,  redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from .forms import UserRegisterForm, ProductForm, ReviewForm
from django.contrib import messages
from .models import UserProfile, Product, Category, ProductReview
from django.http import HttpResponseForbidden
from django.db.models import Q
from django.contrib.auth.views import LoginView
from django.utils.decorators import method_decorator


def logout_required(function):
    def wrap(request, *args, **kwargs):
        if request.user.is_authenticated:
            # Redirect to homepage if user is logged in
            return redirect('home')
        else:
            return function(request, *args, **kwargs)
    return wrap


@logout_required
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


@method_decorator(logout_required, name='dispatch')
class CustomLoginView(LoginView):
    template_name = 'ecommerce/login.html'


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
    products = Product.objects.all()
    categories = Category.objects.all()

    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | Q(
                description__icontains=search_query)
        )

    # Filter
    category_query = request.GET.get('category', '')
    if category_query:
        products = products.filter(categories__name=category_query)

    # Sort
    sort_by = request.GET.get('sort_by', '')
    if sort_by:
        if sort_by == 'price_asc':
            products = products.order_by('price')
        elif sort_by == 'price_desc':
            products = products.order_by('-price')

    context = {
        'products': products,
        'categories': categories,
    }
    return render(request, 'ecommerce/home.html', context)


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


@login_required
def product_detail(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    reviews = ProductReview.objects.filter(product=product)

    if request.method == 'POST':
        review_form = ReviewForm(request.POST)
        if review_form.is_valid():
            new_review = review_form.save(commit=False)
            new_review.product = product
            new_review.user = request.user
            new_review.save()
            messages.success(request, 'Review added successfully!')
            return redirect('product_detail', product_id=product.id)
    else:
        review_form = ReviewForm()

    context = {
        'product': product,
        'reviews': reviews,
        'review_form': review_form,
    }
    return render(request, 'ecommerce/product_detail.html', context)
