from django.shortcuts import render,  redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from .forms import UserRegisterForm, ProductForm, ReviewForm
from django.contrib import messages
from .models import UserProfile, Product, Category, ProductReview, Cart, CartItem, Wishlist, Order, OrderDetails
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

    product = get_object_or_404(Product, pk=product_id)

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

    product.total_views += 1
    product.save()

    context = {
        'product': product,
        'reviews': reviews,
        'review_form': review_form,
    }
    return render(request, 'ecommerce/product_detail.html', context)


@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    quantity = int(request.POST.get('quantity', 1))

    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart, product=product)

    if created:
        cart_item.quantity = quantity
    else:
        cart_item.quantity += quantity
    cart_item.save()

    product.inventory.current_stock -= quantity
    product.inventory.save()

    messages.success(request, 'Product added to cart!')
    return redirect('product_detail', product_id=product.id)


@login_required
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
    wishlist.products.add(product)
    messages.success(request, 'Product added to wishlist!')
    return redirect('product_detail', product_id=product.id)


@login_required
def cart(request):
    cart = Cart.objects.filter(user=request.user).first()
    cart_items = CartItem.objects.filter(cart=cart)
    total_price = sum(item.product.price *
                      item.quantity for item in cart_items)

    if request.method == 'POST':
        # Process the order
        order = Order.objects.create(
            user=request.user, total_amount=total_price)
        for item in cart_items:
            OrderDetails.objects.create(
                order=order, product=item.product, quantity=item.quantity, price=item.product.price)
        cart_items.delete()
        messages.success(request, 'Order placed successfully!')
        return redirect('home')

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
    }
    return render(request, 'ecommerce/cart.html', context)


def calculate_vendor_stats(vendor):
    total_sales = 0
    total_orders = 0
    total_views = 0

    for product in vendor.products.all():
        total_views += product.total_views
        order_details = OrderDetails.objects.filter(product=product)
        total_orders += order_details.count()
        total_sales += sum(detail.price *
                           detail.quantity for detail in order_details)

    conversion_rate = (total_orders / total_views) * \
        100 if total_views > 0 else 0

    return {
        'total_sales': total_sales,
        'total_orders': total_orders,
        'total_views': total_views,
        'conversion_rate': conversion_rate,
    }


@login_required
@vendor_required
def vendor_home(request):
    vendor = request.user
    stats = calculate_vendor_stats(vendor)

    top_selling_products = ...
    sales_data = ...
    projected_data = ...

    context = {
        'total_sales': stats['total_sales'],
        'total_orders': stats['total_orders'],
        'total_views': stats['total_views'],
        'conversion_rate': stats['conversion_rate'],
        'top_selling_products': top_selling_products,
        'sales_data': sales_data,
        'projected_data': projected_data,
    }

    return render(request, 'ecommerce/vendor_page.html', context)
