from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator

User = get_user_model()


class Feedback(models.Model):
    author = models.ForeignKey(User, verbose_name='Автор', on_delete=models.CASCADE, related_name='feedbackauthor', null=True)
    topic = models.CharField(verbose_name='Тема', blank=False, max_length=255)
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

    file = models.FileField(verbose_name='Файл', upload_to='files', validators=[FileExtensionValidator(allowed_extensions=['doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'pdf'])], blank=True)
    pub_date = models.DateTimeField(verbose_name='Время добавления', auto_now_add=True)
    description = models.TextField(verbose_name='Описание', blank=False)
    status = models.CharField(
        verbose_name="Статус",
        max_length=50,
        choices=[('new', 'Новая'), ('in_processing', 'В обработке'), ('accept', 'Принята'), ('rejected', 'Отклонена')],
        default='new')

    class Meta:
        verbose_name = 'Предложение'
        verbose_name_plural = 'Предложения'
        ordering = ['-pk']


class Recipient(models.Model):
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.email