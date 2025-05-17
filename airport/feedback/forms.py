from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
from django import forms
from django.core.exceptions import ValidationError
import os
from .models import Feedback, Recipient
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from . import models
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

EMPTY = '-пусто-'


class RecipientForm(forms.ModelForm):
    class Meta:
        model = Recipient
        fields = ['email']


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'password1', 'password2']


class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), label="Повторите пароль")
    first_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}), label="Введите имя")
    last_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}), label="Введите фамилию")
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}), label="Введите фамилию")

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'password']

    def clean_confirm_password(self):
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')

        if password != confirm_password:
            raise ValidationError("Пароли не совпадают.")

    def clean_email(self):
        email = self.cleaned_data['email']
        return email


class ChangePasswordForm(forms.ModelForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), label="Повторите пароль")

    class Meta:
        model = User
        fields = ['password']
    

    def clean_email(self):
        # Переопределяем валидацию email, чтобы она не проверяла уникальность
        return self.cleaned_data.get('email')

    def clean_confirm_password(self):
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')

        if password != confirm_password:
            raise ValidationError("Пароли не совпадают.")


class OfferAddForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['file', 'description', 'department', 'topic']
    
    anonymous = forms.BooleanField(required=False, label='Отправить анонимно')


class OfferEditForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['file', 'description', 'department', 'topic', 'status']


class MyUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = models.User
        fields = '__all__'


class MyUserAdmin(UserAdmin):
    form = MyUserChangeForm
    add_form = UserCreationForm  # Добавляем форму создания пользователя
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2', 'department', 'role'),
        }),
    )

    # Поля, которые отображаются в профиле пользователя
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'department', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    list_display = [
        'id',
        'email',
        'first_name',
        'last_name',
        'department',
        'role'
    ]
    search_fields = ['id', 'email', 'first_name', 'last_name']
    list_filter = ['is_superuser', 'is_active', 'groups', 'department', 'role']
    list_per_page = 12
    empty_value_display = EMPTY


admin.site.register(models.User, MyUserAdmin)

class FeedbackAdmin(admin.ModelAdmin):
    list_display = [
        'id',                # ID фидбэка
        'author',            # Автор фидбэка
        'topic',
        'pub_date',          # Дата публикации
        'description',       # Описание
        'status',            # Статус фидбэка
        'file',              # Файл (если есть)
    ]
    
    # Настройка полей для поиска
    search_fields = ['id', 'author__username', 'author__email', 'description']
    
    # Фильтры на странице списка
    list_filter = ['status', 'pub_date', 'author__is_active']
    
    # Количество объектов на странице
    list_per_page = 12
    
    # Настройка отображения пустых значений
    empty_value_display = '-пусто-'

admin.site.register(Feedback, FeedbackAdmin)