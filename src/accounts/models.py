from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication."""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user with the given email and password."""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model with email as the unique identifier."""
    
    email = models.EmailField(db_index=True, null=True, blank=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    
    # Anonymous user fields
    is_anonymous = models.BooleanField(default=False, db_index=True)
    device_id = models.CharField(max_length=255, unique=True, null=True, blank=True, db_index=True)
    
    # Social authentication fields
    auth_provider = models.CharField(
        max_length=50,
        default='email',
        choices=[
            ('email', 'Email'),
            ('google', 'Google'),
            ('apple', 'Apple'),
            ('anonymous', 'Anonymous'),
        ]
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']

    def __str__(self):
        if self.is_anonymous:
            return f'Anonymous User ({self.device_id})'
        return self.email or f'User {self.id}'

    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        if self.is_anonymous:
            return 'Anonymous User'
        return f'{self.first_name} {self.last_name}'.strip() or self.email or f'User {self.id}'
    
    def save(self, *args, **kwargs):
        """Override save to validate email uniqueness for non-anonymous users."""
        if self.email and not self.is_anonymous:
            # Check email uniqueness for non-anonymous users
            existing = User.objects.filter(email=self.email, is_anonymous=False).exclude(pk=self.pk)
            if existing.exists():
                from django.core.exceptions import ValidationError
                raise ValidationError({'email': 'User with this email already exists.'})
        super().save(*args, **kwargs)
