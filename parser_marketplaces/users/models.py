from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from phonenumber_field.modelfields import PhoneNumberField

class User(AbstractUser):
    photo = models.ImageField(upload_to="users/%Y/%m/%d/", blank=True, null=True, verbose_name="Фотография", default='users/default.png')
    date_birth = models.DateField(blank=True, null=True, verbose_name="Дата рождения")
    phone = PhoneNumberField(
        verbose_name="Номер телефона",
        help_text="Введите номер в международном формате, например +79012345678",
        blank=True,          # allow optional entry
        null=True,           # allow NULLs in DB
        unique=True
    )

    telegram_username_validator = RegexValidator(
        regex=r'^@[A-Za-z0-9_]{5,32}$',
        message="Введите корректный Telegram-логин. Он должен начинаться с @ и содержать от 5 до 32 символов."
    )
    telegram_username = models.CharField(
        verbose_name="Telegram Username",
        max_length=35,
        validators=[telegram_username_validator],
        blank=True,
        null=True,
        unique=True
    )

    def __str__(self):
        return f"Профиль пользователя: {self.phone}"