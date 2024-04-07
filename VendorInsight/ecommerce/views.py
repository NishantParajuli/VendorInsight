from django.shortcuts import render,  redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from .forms import UserRegisterForm, ProductForm, ReviewForm, SalesFilterForm
from django.contrib import messages
from .models import UserProfile, Product, Category, ProductReview, Cart, CartItem, Wishlist, Order, OrderDetails, User
from django.http import HttpResponseForbidden
from django.db.models import Q, Sum, F
from django.contrib.auth.views import LoginView
from django.utils.decorators import method_decorator
from django.utils import timezone
from datetime import timedelta
from django.core.paginator import Paginator


import pandas as pd
import numpy as np
from pmdarima import auto_arima
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.cluster import KMeans
from xgboost import XGBRegressor
from django.db.models import Count


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

    # Pagination
    paginator = Paginator(products, 9)  # Show 9 products per page
    page = request.GET.get('page')
    products = paginator.get_page(page)

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

    form = SalesFilterForm(request.GET)
    selected_range = form.data.get('range')

    time_ranges = {
        '7_days': timedelta(days=7),
        '1_month': timedelta(days=30),
        '3_months': timedelta(days=90),
        '6_months': timedelta(days=180),
        '1_year': timedelta(days=365),
        '5_years': timedelta(days=1825),
    }

    if selected_range in time_ranges:
        time_threshold = timezone.now() - time_ranges[selected_range]
        order_details = OrderDetails.objects.filter(
            product__user=vendor,
            order__order_date__gte=time_threshold
        )
    else:
        order_details = OrderDetails.objects.filter(product__user=vendor)

    top_selling_products = order_details.values('product__name').annotate(
        total_quantity=Sum('quantity')
    ).order_by('-total_quantity')[:5]

    sales_data = order_details.values('order__order_date').annotate(
        total_sales=Sum(F('price') * F('quantity'))
    ).order_by('order__order_date')

    # Prepare the sales data for Chart.js
    labels = [data['order__order_date'].strftime(
        '%Y-%m-%d') for data in sales_data]
    data = [float(data['total_sales']) for data in sales_data]

    context = {
        'form': form,
        'total_sales': stats['total_sales'],
        'total_orders': stats['total_orders'],
        'total_views': stats['total_views'],
        'conversion_rate': stats['conversion_rate'],
        'top_selling_products': top_selling_products,
        'sales_data': sales_data,
        'labels': labels,
        'data': data,
    }

    return render(request, 'ecommerce/vendor_page.html', context)


@login_required
@vendor_required
def vendor_analytics(request):
    vendor = request.user
    products = vendor.products.all()

    # Sales prediction using Auto ARIMA
    order_details = OrderDetails.objects.filter(product__user=vendor)
    sales_data = pd.DataFrame(list(order_details.values(
        'order__order_date', 'price', 'quantity')))
    sales_data['order__order_date'] = pd.to_datetime(
        sales_data['order__order_date'])
    sales_data['sales'] = sales_data['price'] * sales_data['quantity']
    ts_data = sales_data.groupby(pd.Grouper(key='order__order_date', freq='D'))[
        'sales'].sum()

    ts_data_log = np.log(ts_data.astype(float) + 1)
    model = auto_arima(ts_data_log, seasonal=True,
                       m=12, suppress_warnings=True)

    last_date = ts_data.index[-1]
    future_dates_sales = pd.date_range(
        start=last_date + pd.Timedelta(days=1), periods=30, freq='D')
    future_predictions_sales = np.exp(
        model.predict(n_periods=len(future_dates_sales)))

    # Customer segmentation using K-means
    customer_orders = Order.objects.filter(orderdetails__product__user=vendor).values('user').annotate(
        total_spent=Sum(F('orderdetails__price') *
                        F('orderdetails__quantity')),
        order_count=Count('id')
    )

    customer_data = []
    for order in customer_orders:
        user = User.objects.get(id=order['user'])
        age = (timezone.now().date() -
               user.userprofile.date_of_birth).days // 365
        most_ordered_category = OrderDetails.objects.filter(order__user=user).values(
            'product__categories__name').annotate(count=Count('id')).order_by('-count').first()['product__categories__name']
        customer_data.append({
            'user_id': user.id,
            'age': age,
            'total_order_amount': order['total_spent'],
            'order_frequency': order['order_count'],
            'gender': user.userprofile.gender,
            'most_ordered_category': most_ordered_category
        })

    features_df = pd.DataFrame(customer_data)
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), [
             'age', 'total_order_amount', 'order_frequency']),
            ('cat', OneHotEncoder(), ['gender', 'most_ordered_category'])
        ])
    X_processed = preprocessor.fit_transform(features_df)

    kmeans = KMeans(n_clusters=4, random_state=42)
    clusters = kmeans.fit_predict(X_processed)
    features_df['cluster'] = clusters

    # Inventory prediction using XGBoost
    inventory_data = []
    for product in products:
        daily_sales = pd.DataFrame(list(OrderDetails.objects.filter(
            product=product).values('order__order_date', 'quantity')))
        daily_sales['order__order_date'] = pd.to_datetime(
            daily_sales['order__order_date'])
        daily_sales['day_of_week'] = daily_sales['order__order_date'].dt.dayofweek
        daily_sales['month'] = daily_sales['order__order_date'].dt.month

        X = daily_sales[['day_of_week', 'month']]
        y = daily_sales['quantity']

        xgb_model = XGBRegressor(objective='reg:squarederror',
                                 n_estimators=100, learning_rate=0.1, random_state=42)
        xgb_model.fit(X, y)

        future_dates = pd.date_range(start=daily_sales['order__order_date'].max(
        ) + pd.Timedelta(days=1), periods=7, freq='D')
        future_data = pd.DataFrame({
            'day_of_week': future_dates.dayofweek,
            'month': future_dates.month
        })
        future_predictions = xgb_model.predict(future_data)
        print(future_predictions.tolist())

        inventory_data.append({
            'product_name': product.name,
            'current_stock': product.inventory.current_stock,
            'safety_stock_level': product.inventory.safety_stock_level,
            'reorder_point': product.inventory.reorder_point,
            'future_predictions': future_predictions.tolist()
        })

    context = {
        'sales_dates': future_dates_sales.strftime('%Y-%m-%d').tolist(),
        'sales_predictions': future_predictions_sales.tolist(),
        'customer_segmentation': features_df.to_dict(orient='records'),
        'inventory_data': inventory_data
    }

    return render(request, 'ecommerce/vendor_analytics.html', context)
