from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import CustomLoginForm
from .forms import SignupForm
from django.contrib.auth import logout
from django.shortcuts import redirect
def login_view(request):
    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = CustomLoginForm()

    return render(request, 'login/login.html', {'form': form})



def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = SignupForm()

    return render(request, 'login/signup.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login') 

