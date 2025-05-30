from django.db import models
from django.contrib.auth.models import User

class Service(models.Model):
    name = models.CharField(max_length=100)
    image = models.URLField()
    description = models.TextField()
    is_deleted = models.BooleanField(default=False) 
   
    def __str__(self):
        return self.name

class Application(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('deleted', 'Удалён'),
        ('generated', 'Сформирован'),
        ('completed', 'Завершён'),
        ('rejected', 'Отклонён'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Создатель заявки (пользователь)
    moderator = models.ForeignKey(User, related_name='moderated_applications', on_delete=models.CASCADE, null=True, blank=True)  # Модератор заявки
    created_at = models.DateTimeField(auto_now_add=True)  # Дата создания
    generated_at = models.DateTimeField(null=True, blank=True)  # Дата формирования
    completed_at = models.DateTimeField(null=True, blank=True)  # Дата завершения
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')  # Статус заявки
    is_deleted = models.BooleanField(default=False)  # Логическое удаление заявки

    def __str__(self):
        return f"Заявка #{self.pk} от {self.user.username}"

# Модель пользователя
class User(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    role = models.CharField(max_length=50)

class ApplicationService(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)

    class Meta:
        # Составной первичный ключ из двух внешних ключей
        unique_together = ('application', 'service')

    def __str__(self):
        return f"Заявка #{self.application.pk} - Услуга: {self.service.name}"
