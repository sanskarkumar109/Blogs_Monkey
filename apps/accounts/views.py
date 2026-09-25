from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import View, DetailView
from django.utils.decorators import method_decorator

from .models import User, Profile, UserStatus
from .forms import UserRegistrationForm, UserLoginForm, ProfileUpdateForm, UserUpdateForm

class RegisterView(View):
    template_name = 'accounts/register.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard:home')
        form = UserRegistrationForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard:home')
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to BlogSaaS, {user.username}! Your account has been created.")
            return redirect('dashboard:home')
        return render(request, self.template_name, {'form': form})


class CustomLoginView(View):
    template_name = 'accounts/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard:home')
        form = UserLoginForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard:home')
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user is not None:
                if user.status == UserStatus.SUSPENDED:
                    messages.error(request, "Your account has been suspended. Please contact platform administrators.")
                    return render(request, self.template_name, {'form': form})
                
                login(request, user)
                messages.success(request, f"Welcome back, {user.username}!")
                next_url = request.GET.get('next') or 'dashboard:home'
                return redirect(next_url)
        else:
            messages.error(request, "Invalid username/email or password.")
        return render(request, self.template_name, {'form': form})


class CustomLogoutView(View):
    def get(self, request):
        logout(request)
        messages.info(request, "You have been logged out successfully.")
        return redirect('blog:home')

    def post(self, request):
        logout(request)
        messages.info(request, "You have been logged out successfully.")
        return redirect('blog:home')


@method_decorator(login_required, name='dispatch')
class ProfileEditView(View):
    template_name = 'accounts/profile_edit.html'

    def get(self, request):
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)
        return render(request, self.template_name, {
            'user_form': user_form,
            'profile_form': profile_form
        })

    def post(self, request):
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect('accounts:profile_edit')
        return render(request, self.template_name, {
            'user_form': user_form,
            'profile_form': profile_form
        })
