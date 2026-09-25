from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserRole(models.TextChoices):
    ADMIN = 'admin', 'Admin'
    AUTHOR = 'author', 'Author'

class UserStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    SUSPENDED = 'suspended', 'Suspended'

class User(AbstractUser):
    email = models.EmailField(unique=True, verbose_name='Email Address')
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.AUTHOR,
        db_index=True
    )
    status = models.CharField(
        max_length=20,
        choices=UserStatus.choices,
        default=UserStatus.ACTIVE,
        db_index=True
    )

    REQUIRED_FIELDS = ['email']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    @property
    def is_site_admin(self) -> bool:
        return self.role == UserRole.ADMIN or self.is_superuser

    @property
    def is_active_user(self) -> bool:
        return self.is_active and self.status == UserStatus.ACTIVE

    def __str__(self) -> str:
        return f"{self.username} ({self.get_role_display()})"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, max_length=500, help_text='Short biography')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    website = models.URLField(blank=True)
    twitter_handle = models.CharField(max_length=50, blank=True)
    github_handle = models.CharField(max_length=50, blank=True)
    email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Profile of {self.user.username}"

    @property
    def avatar_url(self) -> str:
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url
        # Modern ui avatar fallback
        name = self.user.get_full_name() or self.user.username
        return f"https://ui-avatars.com/api/?name={name}&background=6366f1&color=fff&bold=true"


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()
