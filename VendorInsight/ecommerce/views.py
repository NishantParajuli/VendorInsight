from django.shortcuts import render,  redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from .forms import UserRegisterForm
from django.contrib import messages


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
            # Redirect to the home page or wherever you prefer
            return redirect('home')
    else:
        form = UserRegisterForm()
    return render(request, 'ecommerce/register.html', {'form': form})


@login_required  # This is a decorator that will redirect to the login page if the user is not logged in
def home(request):
    return render(request, 'ecommerce/home.html')
