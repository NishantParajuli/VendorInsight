from django.urls import path
from .views import register, home, vendor_home, add_product, CustomLoginView, product_detail, add_to_cart, add_to_wishlist, cart
from django.contrib.auth.views import LoginView, LogoutView

urlpatterns = [
    path('register/', register, name='register'),
    path('', home, name='home'),
]

urlpatterns += [
    path('accounts/login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('vendor/home/', vendor_home, name='vendor_home'),
    path('vendor/add_product/', add_product, name='add_product'),
    path('product/<int:product_id>/', product_detail, name='product_detail'),
    path('add_to_cart/<int:product_id>/', add_to_cart, name='add_to_cart'),
    path('add_to_wishlist/<int:product_id>/',
         add_to_wishlist, name='add_to_wishlist'),
    path('cart/', cart, name='cart'),
]
