from django.urls import path
from .views import register, home
from django.contrib.auth.views import LoginView, LogoutView

urlpatterns = [
    path('register/', register, name='register'),
    path('', home, name='home')
]

urlpatterns += [
    path('accounts/login/',
         LoginView.as_view(template_name='ecommerce/login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
