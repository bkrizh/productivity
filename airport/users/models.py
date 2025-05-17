from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.db.models import Q


class CustomUserManager(UserManager):
    def create_superuser(self, email, first_name, last_name, password=None, **extra_fields):
        # Если не указан пароль, выбрасываем исключение
        if not email:
            raise ValueError("The Email field must be set")
        
        email = self.normalize_email(email)
        user = self.model(email=email, first_name=first_name, last_name=last_name, **extra_fields)
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user
        
    
    

class User(AbstractUser):
    """ Модель пользователя. """
    email = models.EmailField(
        verbose_name="Электронная почта",
        max_length=254,
        unique=True
    )
    first_name = models.CharField(
        verbose_name="Имя",
        max_length=150
    )
    last_name = models.CharField(
        verbose_name="Фамилия",
        max_length=150
    )
    role = models.CharField(
        verbose_name="Роль",
        max_length=50,
        choices=[('empty', 'Нет'), ('admin', 'Администратор')],
        default='empty'
    )
    department = models.CharField(
    verbose_name="Отдел", 
    max_length=50,
    choices=[
        ('empty', 'Не выбрано'),
        ('accept', 'Здравпункт'),
        ('KD', 'Коммерческая дирекция (КД)'),
        ('OS', 'Отдел снабжения (ОС)'),
        ('ORP', 'Отдел по работе с персоналом (ОРП)'),
        ('FEO', 'Финансово-экономический отдел (ФЭО)'),
        ('OHR', 'Охрана труда (ОТ)'),
        ('PR', 'Пресс-служба (PR)')
    ], 
    default='empty'
)



    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [
        'first_name',
        'last_name']
    
    objects = CustomUserManager()

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.email  # Устанавливаем username равным email, если оно пустое
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['-pk']


