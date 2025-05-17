from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied, BadRequest
from .models import Feedback, Recipient
from .forms import OfferAddForm, OfferEditForm, ChangePasswordForm, RecipientForm
from django.conf import settings
from django.http import FileResponse
from django.contrib import messages
import os
from django.db import transaction
from django.utils import timezone
from django.http import HttpResponse
from django.core.paginator import Paginator
from datetime import datetime
from .forms import RegistrationForm
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
from users.models import User
import xlwt
from django.utils.timezone import localtime


def handler404(request, exception):
    """
    Обработка ошибки 404
    """
    return render(request=request, template_name='users/errors.html', status=404, context={
        'title': 'Страница не найдена: 404',
        'error_message': 'Такой страницы не существует, или она перемещена.',
    })


def handler403(request, exception):
    """
    Обработка ошибки 403
    """
    return render(request=request, template_name='users/errors.html', status=403, context={
        'title': 'Ошибка доступа: 403',
        'error_message': 'Доступ к этой странице ограничен.',
    })


def success(request):
    context = {}
    messages_list = list(messages.get_messages(request))
    context['success_message'] = next((msg.message for msg in messages_list if msg.level == messages.SUCCESS), None)
    context['error_message'] = next((msg.message for msg in messages_list if msg.level == messages.ERROR), None)
    messages.get_messages(request).used = True
    return render(request, 'offers/success.html', context)


def error(request):
    context = {}
    messages_list = list(messages.get_messages(request))
    context['success_message'] = next((msg.message for msg in messages_list if msg.level == messages.SUCCESS), None)
    context['error_message'] = next((msg.message for msg in messages_list if msg.level == messages.ERROR), None)
    messages.get_messages(request).used = True
    return render(request, 'offers/error.html', context)


def reset_password(request):
    request.session.flush()
    if request.method == 'POST':
        form = ChangePasswordForm(request.POST)
        password = request.POST.get('password')
        context = {}
        if form.is_valid():
            password = form.cleaned_data['password']
            email = form.cleaned_data['email']
            user = User.objects.filter(email=email).first()
            if not user:
                messages.error(request, 'Аккаунта с таким адресом электронной почты не существует. Пожалуйста, зарегистрируйтесь.')
                return redirect('feedback:register')
            request.session['password'] = password
            request.session['verification_email'] = email
            # Сохраняем код подтверждения в сессии
            code = str(random.randint(100000, 999999))
            request.session['verification_code'] = code
            context = {'form': form}
        
            html_message = f"""
                <html>
                <head>
                    <style>
                        body {{
                            font-family: PTSans, sans-serif;
                            color: #333333;
                        }}
                        .content {{
                            margin-top: 10px;
                            font-size: 16px;
                        }}
                        .footer {{
                            margin-top: 30px;
                            font-size: 14px;
                            color: #777777;
                            border-top: 1px solid #ddd;
                            padding-top: 10px;
                            text-align: center;
                        }}
                        a {{
                            color: #228b22;
                            text-decoration: none;
                        }}
                        a:hover {{
                            text-decoration: underline;
                        }}
                    </style>
                </head>
                <body>
                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                        <tr>
                            <td>
                                <table role="presentation" width="600" cellspacing="0" cellpadding="0" border="0" style="border: 2px solid #800080; border-radius: 8px; background-color: #ffffff;">
                                    <tr>
                                        <td style="padding: 20px;">
                                            <div class="content">
                                                <p>Поступил запрос на смену пароля аккаунта в Сервисе обратной связи.</p>
                                                <p>Ваш код подтверждения для смены пароля: {code}</p>
                                                <p>Если запрос на смену пароля аккаунта отправили не вы, ничего не делайте с этим письмом.</p>
                                            </div>
                                            <div class="footer">
                                                <p>Это сообщение было сгенерировано автоматически, отвечать на него не нужно.</p>
                                            </div>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                    </table>
                </body>
                </html>
                """
            send_custom_email(subject=f"Смена пароля пользователя в Сервисе обратной связи", body="Текст письма", recipient_email=user.email, html_message=html_message)

            messages.success(request, 'На вашу почту отправлен код подтверждения.')
            return redirect('feedback:verify_password')  # Перенаправляем на страницу ввода кода
        else:
            # form = ChangePasswordForm()
            context = {'form': form}
            messages.error(request, f'{form.errors}')
    else:
        form = ChangePasswordForm()
        context = {'form': form}
        messages_list = list(messages.get_messages(request))
        context['success_message'] = next((msg.message for msg in messages_list if msg.level == messages.SUCCESS), None)
        context['error_message'] = next((msg.message for msg in messages_list if msg.level == messages.ERROR), None)
        messages.get_messages(request).used = True
    return render(request, 'offers/reset_password.html', context)


def verify_password(request):
    if request.method == 'POST':
        verification_email = request.session.get('verification_email')
        input_code = request.POST.get('verification_code')
        saved_code = request.session.get('verification_code')


        if input_code == saved_code:
            # Подтверждаем пароль
            user = User.objects.filter(email=verification_email).first()
            password = request.session.get('password')
            user.set_password(password)
            user.is_active = True
            user.save()

            messages.success(request, 'Ваш пароль изменен! Теперь вы можете войти в систему.')
            return redirect('feedback:success')
        else:
            messages.error(request, 'Неверный код подтверждения. Попробуйте снова.')
    else:
        context = {}
        messages_list = list(messages.get_messages(request))
        context['success_message'] = next((msg.message for msg in messages_list if msg.level == messages.SUCCESS), None)
        context['error_message'] = next((msg.message for msg in messages_list if msg.level == messages.ERROR), None)
        messages.get_messages(request).used = True
    return render(request, 'offers/verify_password.html', context)


def verify_email(request):
    if request.method == 'POST':
        verification_email = request.session.get('verification_email')
        input_code = request.POST.get('verification_code')
        saved_code = request.session.get('verification_code')


        if input_code == saved_code:
            # Подтверждаем аккаунт
            user = User.objects.filter(email=verification_email).first()
            user.is_active = True
            user.save()

            messages.success(request, 'Ваш email подтвержден! Теперь вы можете войти в систему.')
            return redirect('feedback:success')
        else:
            # messages.error(request, 'Неверный код подтверждения. Попробуйте снова.')
            return render(request, 'offers/verify_email.html')
    else:
        context = {}
        messages_list = list(messages.get_messages(request))
        context['success_message'] = next((msg.message for msg in messages_list if msg.level == messages.SUCCESS), None)
        context['error_message'] = next((msg.message for msg in messages_list if msg.level == messages.ERROR), None)
        messages.get_messages(request).used = True

    return render(request, 'offers/verify_email.html', context)


def register(request):
    request.session.flush()
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        # Получаем email из формы до проверки валидации
        context = {}
        email = request.POST.get('email')
        password = request.POST.get('password')  # Получаем пароль из формы
        confirm_password = request.POST.get('confirm_password')  # Получаем пароль из формы
        if email and (password == confirm_password):
            # Попробуем найти существующего пользователя с данным email
            existing_user = User.objects.filter(email=email).first()

            if existing_user:
                if existing_user.is_active == False:
                    # Пользователь существует, но не активен. Отправляем новый код активации.
                    code = str(random.randint(100000, 999999))
                    request.session['verification_email'] = email
                    existing_user.is_active = True
                    existing_user.set_password(password)
                    existing_user.save()
                    existing_user.is_active = False
                    existing_user.save()
                    request.session['verification_code'] = code

                    # Генерация кода активации
                    html_message = f"""
                            <html>
                            <head>
                                <style>
                                    body {{
                                        font-family: PTSans, sans-serif;
                                        color: #333333;
                                    }}
                                    .content {{
                                        margin-top: 10px;
                                        font-size: 16px;
                                    }}
                                    .footer {{
                                        margin-top: 30px;
                                        font-size: 14px;
                                        color: #777777;
                                        border-top: 1px solid #ddd;
                                        padding-top: 10px;
                                        text-align: center;
                                    }}
                                    a {{
                                        color: #228b22;
                                        text-decoration: none;
                                    }}
                                    a:hover {{
                                        text-decoration: underline;
                                    }}
                                </style>
                            </head>
                            <body>
                                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                                    <tr>
                                        <td>
                                            <table role="presentation" width="600" cellspacing="0" cellpadding="0" border="0" style="border: 2px solid #800080; border-radius: 8px; background-color: #ffffff;">
                                                <tr>
                                                    <td style="padding: 20px;">
                                                        <div class="content">
                                                            <p>Поступил запрос на активацию аккаунта в Сервисе обратной связи.</p>
                                                            <p>Ваш новый код подтверждения для активации аккаунта: {code}</p>
                                                            <p>Если запрос на создание аккаунта отправили не вы, ничего не делайте с этим письмом.</p>
                                                        </div>
                                                        <div class="footer">
                                                            <p>Это сообщение было сгенерировано автоматически, отвечать на него не нужно.</p>
                                                        </div>
                                                    </td>
                                                </tr>
                                            </table>
                                        </td>
                                    </tr>
                                </table>
                            </body>
                            </html>
                            """
                    send_custom_email(
                        subject="Повторный код активации аккаунта",
                        body="",
                        recipient_email=email,
                        html_message=html_message,
                    )

                    messages.success(request, 'На указанный email уже зарегистрирован аккаунт, но не активирован. Новый код подтверждения для активации аккаунта отправлен.')
                    return redirect('feedback:verify_email')
                else:
                    # Если пользователь активен, перенаправляем его на логин
                    messages.error(request, 'Пользователь с таким email уже активирован. Войдите в систему.')
                    return redirect('feedback:error')
        if form.is_valid():
            # Создание нового пользователя
            email = form.cleaned_data['email']

            user = form.save(commit=False)
            user.set_password(request.POST.get('password'))
            user.is_active = False  # Устанавливаем аккаунт как неактивный
            user.save()

            # Сохраняем код подтверждения в сессии
            code = str(random.randint(100000, 999999))
            request.session['verification_code'] = code
            request.session['verification_email'] = email
            context = {'form': form}
        
            html_message = f"""
                <html>
                <head>
                    <style>
                        body {{
                            font-family: PTSans, sans-serif;
                            color: #333333;
                        }}
                        .content {{
                            margin-top: 10px;
                            font-size: 16px;
                        }}
                        .footer {{
                            margin-top: 30px;
                            font-size: 14px;
                            color: #777777;
                            border-top: 1px solid #ddd;
                            padding-top: 10px;
                            text-align: center;
                        }}
                        a {{
                            color: #228b22;
                            text-decoration: none;
                        }}
                        a:hover {{
                            text-decoration: underline;
                        }}
                    </style>
                </head>
                <body>
                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                        <tr>
                            <td>
                                <table role="presentation" width="600" cellspacing="0" cellpadding="0" border="0" style="border: 2px solid #800080; border-radius: 8px; background-color: #ffffff;">
                                    <tr>
                                        <td style="padding: 20px;">
                                            <div class="content">
                                                <p>Поступил запрос на создание аккаунта в Сервисе обратной связи.</p>
                                                <p>Ваш код подтверждения для создания аккаунта: {code}</p>
                                                <p>Если запрос на создание аккаунта отправили не вы, ничего не делайте с этим письмом.</p>
                                            </div>
                                            <div class="footer">
                                                <p>Это сообщение было сгенерировано автоматически, отвечать на него не нужно.</p>
                                            </div>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                    </table>
                </body>
                </html>
                """
            send_custom_email(subject=f"Создание нового пользователя в Сервисе обратной связи", body="Текст письма", recipient_email=user.email, html_message=html_message)

            messages.success(request, 'На вашу почту отправлен код подтверждения.')
            return redirect('feedback:verify_email')  # Перенаправляем на страницу ввода кода
        else:
            print(form.errors)
            context = {'form': form}
    else:
        form = RegistrationForm()
        context = {'form': form}
        messages_list = list(messages.get_messages(request))
        context['success_message'] = next((msg.message for msg in messages_list if msg.level == messages.SUCCESS), None)
        context['error_message'] = next((msg.message for msg in messages_list if msg.level == messages.ERROR), None)
        messages.get_messages(request).used = True

    return render(request, 'offers/register.html', context)


def send_custom_email(subject, body, recipient_email, html_message=None):
    # Настройки SMTP-сервера
    smtp_server = "192.168.0.1"
    port = 465
    sender_email = "email@test.ru"
    password = "password"

    # Создаем MIME-сообщение
    message = MIMEMultipart("alternative")
    message["From"] = sender_email
    message["To"] = recipient_email
    message["Subject"] = subject

    # Добавляем только HTML-версию, если она задана
    if html_message:
        part = MIMEText(html_message, "html")
        message.attach(part)
    else:
        # Если HTML-сообщение не указано, отправляем простой текст
        part = MIMEText(body, "plain")
        message.attach(part)

    # Настраиваем SSL-контекст без проверки сертификата
    context = ssl._create_unverified_context()

    # Отправляем письмо
    try:
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, recipient_email, message.as_string())
    except Exception as e:
        print(f"Ошибка при отправке письма: {e}")


def send_list_email(subject, body, html_message=None):
    # Настройки SMTP-сервера
    smtp_server = "192.168.0.1"
    port = 465
    sender_email = "email@test.ru"
    password = "password"


    # Получаем все email адреса из модели Recipient
    recipients = Recipient.objects.all()
    recipient_emails = [recipient.email for recipient in recipients]

    # Создаем MIME-сообщение
    message = MIMEMultipart("alternative")
    message["From"] = sender_email
    message["Subject"] = subject

    # Добавляем только HTML-версию, если она задана
    if html_message:
        part = MIMEText(html_message, "html")
        message.attach(part)
    else:
        # Если HTML-сообщение не указано, отправляем простой текст
        part = MIMEText(body, "plain")
        message.attach(part)

    # Настраиваем SSL-контекст без проверки сертификата
    context = ssl._create_unverified_context()

    # Отправляем письмо каждому получателю
    try:
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(sender_email, password)
            for recipient_email in recipient_emails:
                message["To"] = recipient_email
                server.sendmail(sender_email, recipient_email, message.as_string())
    except Exception as e:
        print(f"Ошибка при отправке письма: {e}")


@login_required
def recipients_list(request):
    if not request.user.is_superuser and not request.user.role == 'admin':
        return handler403(request, PermissionDenied)
    recipients = Recipient.objects.all()
    paginator = Paginator(recipients, 8)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'recipients': recipients, 'page_obj': page_obj}
    messages_list = list(messages.get_messages(request))
    context['success_message'] = next((msg.message for msg in messages_list if msg.level == messages.SUCCESS), None)
    context['error_message'] = next((msg.message for msg in messages_list if msg.level == messages.ERROR), None)
    messages.get_messages(request).used = True
    return render(request, 'offers/recipients_list.html', context)


@login_required
def add_recipient(request):
    if not request.user.is_superuser and not request.user.role == 'admin':
        return handler403(request, PermissionDenied)
    if request.method == 'POST':
        form = RecipientForm(request.POST)
        if form.is_valid():
            form.save()
            success_message = "Получатель успешно добавлен."
            messages.success(request, success_message)
            return redirect('feedback:recipients_list')
        else:
            messages.error(request, 'Неправильно указан email, или указанный email уже добавлен в получатели.')
            return redirect('feedback:recipients_list')
    else:
        form = RecipientForm()
    
    return render(request, 'offers/add_recipient.html', {'form': form})


@login_required
def edit_recipient(request, pk):
    if not request.user.is_superuser and not request.user.role == 'admin':
        return handler403(request, PermissionDenied)
    recipient = get_object_or_404(Recipient, pk=pk)
    if request.method == 'POST':
        form = RecipientForm(request.POST, instance=recipient)
        if form.is_valid():
            form.save()
            success_message = "Получатель успешно изменен."
            messages.success(request, success_message)
            return redirect('feedback:recipients_list')
        else:
            messages.error(request, 'Неправильно указан email, или указанный email уже добавлен в получатели.')
            return redirect('feedback:recipients_list')
    else:
        form = RecipientForm(instance=recipient)
    return render(request, 'offers/edit_recipient.html', {'form': form, 'recipient': recipient})


@login_required
def delete_recipient(request, pk):
    if not request.user.is_superuser and not request.user.role == 'admin':
        return handler403(request, PermissionDenied)
    recipient = get_object_or_404(Recipient, pk=pk)
    if request.method == 'POST':
        recipient.delete()
        success_message = "Получатель успешно удален."
        messages.success(request, success_message)
        return redirect('feedback:recipients_list')
    return render(request, 'offers/delete_recipient.html', {'recipient': recipient})


def index(request):
    if not request.user.is_authenticated:
        request.session.flush()
    return render(request, 'offers/index.html', {request.user: 'user'})


@login_required
def export_user_xls(request, offer_id):
    if not request.user.is_superuser and not request.user.role == 'admin':
        return handler403(request, PermissionDenied)
    
    offer = Feedback.objects.filter(id=offer_id)

    if not offer:
        return handler403(request, BadRequest)
    
    offer = get_object_or_404(Feedback, id=offer_id)
    
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="offers.xls"'

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Offers')

    # Sheet header, first row
    row_num = 0
    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    columns = ['Номер заявки', 'Автор', 'Отдел, относящийся к теме', 'Тема', 'Описание', 'Статус', 'Дата']

    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)

    # Filter offers based on the request parameters

    # Write offers data
    font_style = xlwt.XFStyle()

    row_num += 1
    ws.write(row_num, 0, offer.pk, font_style)
    ws.write(row_num, 1, f'{offer.author.get_full_name()} ({offer.author.email})' if offer.author else 'Аноним', font_style)
    ws.write(row_num, 2, offer.get_department_display(), font_style)
    ws.write(row_num, 3, offer.topic, font_style)
    ws.write(row_num, 4, offer.description, font_style)
    ws.write(row_num, 5, offer.get_status_display(), font_style)
    formatted_date = localtime(offer.pub_date).strftime('%Y-%m-%d %H:%M:%S')
    ws.write(row_num, 6, formatted_date, font_style)

    wb.save(response)
    return response


@login_required
def export_users_xls(request):
    if not request.user.is_superuser and not request.user.role == 'admin':
        return handler403(request, PermissionDenied)

    department_filter = request.GET.get('department', None)
    status_filter = request.GET.get('status', None)
    start_date_filter = request.GET.get('start_date', None)
    end_date_filter = request.GET.get('end_date', None)
    anonymous_filter = request.GET.get('anonymous', None)
    not_anonymous_filter = request.GET.get('not_anonymous', None)
    
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="offers.xls"'

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Offers')

    # Sheet header, first row
    row_num = 0
    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    columns = ['Номер заявки', 'Автор', 'Отдел, относящийся к теме', 'Тема', 'Описание', 'Статус', 'Дата']

    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)

    # Filter offers based on the request parameters
    offers = Feedback.objects.all()

    if department_filter:
        offers = offers.filter(department=department_filter)
    if status_filter:
        offers = offers.filter(status=status_filter)
    if start_date_filter:
        start_date = datetime.strptime(start_date_filter, '%Y-%m-%d')
        start_date = timezone.make_aware(start_date)
        offers = offers.filter(pub_date__gte=start_date)
    if end_date_filter:
        end_date = datetime.strptime(end_date_filter, '%Y-%m-%d')
        end_date = timezone.make_aware(end_date.replace(hour=23, minute=59, second=59))
        offers = offers.filter(pub_date__lte=end_date)
    if anonymous_filter:
        offers = offers.filter(author__isnull=True)
    if not_anonymous_filter:
        offers = offers.filter(author__isnull=False)

    # Write offers data
    font_style = xlwt.XFStyle()

    for offer in offers:
        row_num += 1
        ws.write(row_num, 0, offer.pk, font_style)
        ws.write(row_num, 1, f'{offer.author.get_full_name()} ({offer.author.email})' if offer.author else 'Аноним', font_style)
        ws.write(row_num, 2, str(offer.get_department_display()), font_style)
        ws.write(row_num, 3, offer.topic, font_style)
        ws.write(row_num, 4, offer.description, font_style)
        ws.write(row_num, 5, str(offer.get_status_display()), font_style)
        formatted_date = localtime(offer.pub_date).strftime('%Y-%m-%d %H:%M:%S')
        ws.write(row_num, 6, formatted_date, font_style)

    wb.save(response)
    return response
    

@transaction.atomic
@login_required
def all_offers(request):
    if request.user.department != 'empty' or request.user.role == 'admin' or request.user.is_superuser:
        department_filter = request.GET.get('department', None)
        status_filter = request.GET.get('status', None)
        start_date_filter = request.GET.get('start_date', None)
        end_date_filter = request.GET.get('end_date', None)
        anonymous_filter = request.GET.get('anonymous', None)  # Получаем фильтр для анонимных
        not_anonymous_filter = request.GET.get('not_anonymous', None)  # Получаем фильтр для неанонимных
        if request.user.role != 'admin' and not request.user.is_superuser:
            offers = Feedback.objects.filter(department=request.user.department).order_by('-pub_date')
            if status_filter:
                offers = offers.filter(status=status_filter)

            if start_date_filter:
                start_date = datetime.strptime(start_date_filter, '%Y-%m-%d')
                start_date = timezone.make_aware(start_date)  # учитываем часовой пояс
                offers = offers.filter(pub_date__gte=start_date)

            if end_date_filter:
                end_date = datetime.strptime(end_date_filter, '%Y-%m-%d')
                end_date = timezone.make_aware(end_date.replace(hour=23, minute=59, second=59))
                offers = offers.filter(pub_date__lte=end_date)
            

            # Фильтрация по анонимным пользователям
            if anonymous_filter:
                offers = offers.filter(author__isnull=True)  # Фильтровать только анонимных пользователей

            if not_anonymous_filter:
                offers = offers.filter(author__isnull=False)  # Фильтровать только неанонимных пользователей

        else:
            offers = Feedback.objects.all().order_by('-pub_date')
            if department_filter:
                offers = offers.filter(department=department_filter)

            if status_filter:
                offers = offers.filter(status=status_filter)

            if start_date_filter:
                start_date = datetime.strptime(start_date_filter, '%Y-%m-%d')
                start_date = timezone.make_aware(start_date)  # учитываем часовой пояс
                offers = offers.filter(pub_date__gte=start_date)

            if end_date_filter:
                end_date = datetime.strptime(end_date_filter, '%Y-%m-%d')
                end_date = timezone.make_aware(end_date.replace(hour=23, minute=59, second=59))
                offers = offers.filter(pub_date__lte=end_date)

            # Фильтрация по анонимным пользователям
            if anonymous_filter:
                offers = offers.filter(author__isnull=True)  # Фильтровать только анонимных пользователей

            if not_anonymous_filter:
                offers = offers.filter(author__isnull=False)  # Фильтровать только неанонимных пользователей

        paginator = Paginator(offers, 8)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context = {'user': request.user, 'offers': offers, 'page_obj': page_obj}
        messages_list = list(messages.get_messages(request))
        context['success_message'] = next((msg.message for msg in messages_list if msg.level == messages.SUCCESS), None)
        context['error_message'] = next((msg.message for msg in messages_list if msg.level == messages.ERROR), None)
        messages.get_messages(request).used = True
        return render(request, 'offers/all_offers.html', context)
    else:
        return handler403(request, PermissionDenied)
            

@transaction.atomic
@login_required
def offers(request):
    department_filter = request.GET.get('department', None)
    status_filter = request.GET.get('status', None)
    start_date_filter = request.GET.get('start_date', None)
    end_date_filter = request.GET.get('end_date', None)
    offers = Feedback.objects.filter(author=request.user)

    if department_filter:
        offers = offers.filter(department=department_filter)

    if status_filter:
        offers = offers.filter(status=status_filter)

    if start_date_filter:
        start_date = datetime.strptime(start_date_filter, '%Y-%m-%d')
        start_date = timezone.make_aware(start_date)  # учитываем часовой пояс
        offers = offers.filter(pub_date__gte=start_date)

    if end_date_filter:
        end_date = datetime.strptime(end_date_filter, '%Y-%m-%d')
        end_date = timezone.make_aware(end_date.replace(hour=23, minute=59, second=59))
        offers = offers.filter(pub_date__lte=end_date)
    # if department_filter and status_filter:
    #     offers = Feedback.objects.filter(author=request.user, department=department_filter, status=status_filter).order_by('-pub_date')
    # elif department_filter:
    #     offers = Feedback.objects.filter(author=request.user, department=department_filter).order_by('-pub_date')
    # elif status_filter:
    #     offers = Feedback.objects.filter(author=request.user, status=status_filter).order_by('-pub_date')
    # else:
    #     offers = Feedback.objects.filter(author=request.user).order_by('-pub_date')
    paginator = Paginator(offers, 8)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'user': request.user, 'offers': offers, 'page_obj': page_obj}
    messages_list = list(messages.get_messages(request))
    context['success_message'] = next((msg.message for msg in messages_list if msg.level == messages.SUCCESS), None)
    context['error_message'] = next((msg.message for msg in messages_list if msg.level == messages.ERROR), None)
    messages.get_messages(request).used = True
    return render(request, 'offers/offers.html', context)


@transaction.atomic
@login_required
def offer(request, offer_id):
    offer = get_object_or_404(Feedback, id=offer_id)
    if (request.user.department == offer.department) or request.user == offer.author or request.user.role == 'admin' or request.user.is_superuser:
        if offer.file:
            name = os.path.basename(offer.file.path)
        else:
            name = 'Файл отсутствует'
        context = {'user': request.user, 'offer': offer, 'name': name}
        return render(request, 'offers/offer.html', context)
    else:
        return handler403(request, PermissionDenied)


@transaction.atomic
@login_required
def offer_delete(request, offer_id):
    offer = get_object_or_404(Feedback, pk=offer_id)
    if not (offer.author == request.user or request.user.is_superuser or request.user.role == 'admin'):
        return handler403(request, PermissionDenied)
    if request.method == 'POST':
        if offer.file:
            offer_path = offer.file.path
            os.remove(offer_path)
        if request.user == offer.author:
            user_type = 1
        else:
            user_type = 2
        offer.delete()
        success_message = "Предложение успешно удалено."
        messages.success(request, success_message)
        if user_type == 1:
            return redirect('feedback:offers')
        else:
            return redirect('feedback:all_offers')
    if request.user == offer.author or request.user.is_superuser or request.user.role == 'admin':
        return render(request, 'offers/offer_delete.html', {'document_id': offer_id, 'offer': offer})
    else:
        return handler403(request, PermissionDenied)


@transaction.atomic
@login_required
def offer_add(request):
    if request.method == 'GET':
        form = OfferAddForm()
    if request.method == 'POST':
        form = OfferAddForm(request.POST, request.FILES)
        if form.is_valid():
            offer = form.save(commit=False)
            # Установка автора в None, если форма была отправлена анонимно
            if form.cleaned_data.get('anonymous'):
                offer.author = None  # Автор не указывается
            else:
                offer.author = request.user  # Устанавливаем текущего пользователя как автора
            offer.save()
            success_message = "Предложение успешно отправлено."
            messages.success(request, success_message)
            html_message = f"""
                    <html>
                    <head>
                        <style>
                            body {{
                                font-family: PTSans, sans-serif;
                                color: #333333;
                            }}
                            .content {{
                                margin-top: 10px;
                                font-size: 16px;
                            }}
                            .footer {{
                                margin-top: 30px;
                                font-size: 14px;
                                color: #777777;
                                border-top: 1px solid #ddd;
                                padding-top: 10px;
                                text-align: center;
                            }}
                            a {{
                                color: #228b22;
                                text-decoration: none;
                            }}
                            a:hover {{
                                text-decoration: underline;
                            }}
                        </style>
                    </head>
                    <body>
                        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                            <tr>
                                <td>
                                    <table role="presentation" width="600" cellspacing="0" cellpadding="0" border="0" style="border: 2px solid #800080; border-radius: 8px; background-color: #ffffff;">
                                        <tr>
                                            <td style="padding: 20px;">
                                                <div class="content">
                                                    <p>Создано новое предложение №{offer.id} в сервисе Обратной связи</p>
                                                    {f"<p>Автор: Аноним</p>" if offer.author is None else f"<p>Автор: {offer.author.get_full_name()} ({offer.author.email})</p>"}
                                                    <p>Тема: {offer.topic}</p>
                                                    <p>Предложение доступно по <a href="http://192.168.12.189/offer/{offer.id}">ссылке</a>.</p>
                                                </div>
                                                <div class="footer">
                                                    <p>Это сообщение было сгенерировано автоматически, отвечать на него не нужно.</p>
                                                </div>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                        </table>
                    </body>
                    </html>
                    """
            send_list_email(
                subject="Новое предложение в Обратной связи",
                body="",
                html_message=html_message,
            )
            return redirect('feedback:offers')
        else:
            error_message = "Произошла ошибка при сохранении формы.<br>Проверьте данные и попробуйте ввести еще раз."
            messages.error(request, error_message)
            return redirect('feedback:offers')
    return render(request, 'offers/add_offer.html', {'form': form})


@transaction.atomic
def offer_edit(request, offer_id):
    offer = get_object_or_404(Feedback, pk=offer_id)
    if offer.file:
        offer_path = offer.file.path
    else:
        offer_path = ''
    name = os.path.basename(offer_path)
    if not (offer.author == request.user or request.user.is_superuser or request.user.role == 'admin'):
        return handler403(request, PermissionDenied)
    if request.method == 'GET':
        form = OfferEditForm(request.FILES, instance=offer)
        return render(request, 'offers/offer_edit.html', {'form': form, 'offer': offer, 'name': name})
    if request.method == 'POST':
        form = OfferEditForm(request.POST, request.FILES, instance=offer)
        if form.is_valid():
            offer = form.save(commit=False)
            offer.pub_date = timezone.now()
            offer.save()
            if offer_path:
                full_path = offer.file.path
            else:
                full_path = ''
            if full_path != offer_path:
                os.remove(offer_path)
            success_message = "Данные успешно изменены."
            messages.success(request, success_message)
            if request.user == offer.author:
                return redirect('feedback:offers')
            else:
                return redirect('feedback:all_offers')
        else:
            error_message = "Произошла ошибка при сохранении формы. Проверьте данные и попробуйте ввести еще раз."
            messages.error(request, error_message)
            return redirect('feedback:offers')


@login_required
def offer_document_download(request, offer_id):
    offer = get_object_or_404(Feedback, pk=offer_id)
    if not (offer.author == request.user or request.user.department == 'all' or request.user.is_superuser or request.user.role == 'admin'):
        return handler403(request, PermissionDenied)
    file_path = offer.file.path
    file_name = os.path.basename(file_path)
        # Проверяем, существует ли файл
    if not os.path.exists(file_path):
        raise handler404()
    response = FileResponse(open(file_path, 'rb'), as_attachment=True, filename=file_name)
    return response


def protected_media_view(request, path):
    if not request.user.is_authenticated:
        return handler403(request, PermissionDenied)

    full_path = os.path.join(settings.MEDIA_ROOT, path)
    if not os.path.exists(full_path):
        raise handler404(request, BadRequest)

    with open(full_path, 'rb') as f:
        response = HttpResponse(f.read(), content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(full_path)}"'
        return response