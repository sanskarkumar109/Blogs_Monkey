from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import User, Profile

INPUT_CLASS = 'w-full px-3 py-2 rounded-md border border-[#e8e4de] dark:border-[#2e2c2a] bg-[#faf9f7] dark:bg-[#151413] text-[#1a1a1a] dark:text-[#faf9f7] text-xs focus:outline-none focus:border-[#1a1a1a] dark:focus:border-[#faf9f7] transition'

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': INPUT_CLASS,
        'placeholder': 'you@example.com'
    }))
    username = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={
        'class': INPUT_CLASS,
        'placeholder': 'johndoe'
    }))
    first_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={
        'class': INPUT_CLASS,
        'placeholder': 'John'
    }))
    last_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={
        'class': INPUT_CLASS,
        'placeholder': 'Doe'
    }))

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'password1' in self.fields:
            self.fields['password1'].widget.attrs.update({'class': INPUT_CLASS, 'placeholder': '••••••••'})
        if 'password2' in self.fields:
            self.fields['password2'].widget.attrs.update({'class': INPUT_CLASS, 'placeholder': '••••••••'})

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("A user with this email address already exists.")
        return email.lower()


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': INPUT_CLASS,
        'placeholder': 'Username or Email'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': INPUT_CLASS,
        'placeholder': '••••••••'
    }))

    def clean(self):
        username_or_email = self.cleaned_data.get('username')
        if username_or_email and '@' in username_or_email:
            try:
                user_obj = User.objects.get(email__iexact=username_or_email)
                self.cleaned_data['username'] = user_obj.username
            except User.DoesNotExist:
                pass
        return super().clean()


class ProfileUpdateForm(forms.ModelForm):
    bio = forms.CharField(required=False, widget=forms.Textarea(attrs={
        'class': INPUT_CLASS,
        'rows': 3,
        'placeholder': 'Tell readers a bit about yourself...'
    }))
    website = forms.URLField(required=False, widget=forms.URLInput(attrs={
        'class': INPUT_CLASS,
        'placeholder': 'https://yourwebsite.com'
    }))
    twitter_handle = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': INPUT_CLASS,
        'placeholder': '@username'
    }))
    github_handle = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': INPUT_CLASS,
        'placeholder': 'github_username'
    }))
    avatar = forms.ImageField(required=False, widget=forms.FileInput(attrs={
        'class': 'block w-full text-xs text-[#6b6560] dark:text-[#9c9690] file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border border-[#e8e4de] dark:border-[#2e2c2a] file:text-xs file:font-medium file:bg-[#faf9f7] dark:file:bg-[#292725] file:text-[#1a1a1a] dark:file:text-[#faf9f7] hover:file:bg-[#e5e2dc] transition'
    }))

    class Meta:
        model = Profile
        fields = ('bio', 'avatar', 'website', 'twitter_handle', 'github_handle')

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if avatar and hasattr(avatar, 'size'):
            if avatar.size > 5 * 1024 * 1024:
                raise ValidationError("Image file size must be under 5MB.")
            allowed_types = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
            if hasattr(avatar, 'content_type') and avatar.content_type not in allowed_types:
                raise ValidationError("Unsupported image format. Please upload JPEG, PNG, WEBP, or GIF.")
        return avatar


class UserUpdateForm(forms.ModelForm):
    first_name = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': INPUT_CLASS
    }))
    last_name = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': INPUT_CLASS
    }))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': INPUT_CLASS
    }))

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

