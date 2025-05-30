from django.db import models
from django.contrib.auth.models import AbstractUser, User

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
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    moderator = models.ForeignKey(User, related_name='moderated_applications', 
                                on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    generated_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"Заявка #{self.pk} от {self.user.username}"

class ApplicationService(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('application', 'service')

    def __str__(self):
        return f"Заявка #{self.application.pk} - Услуга: {self.service.name}"