from rest_framework import serializers
from .models import Service, Application, ApplicationService, User

class ServiceSerializer(serializers.ModelSerializer):
    draft_application_id = serializers.SerializerMethodField()

    class Meta:
        model = Service
        fields = ['id', 'name', 'description', 'image', 'is_deleted', 'draft_application_id']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Если метод запроса - PUT или PATCH, то сделаем поля необязательными
        if self.context['request'].method in ['PUT', 'PATCH']:
            for field in self.fields:
                self.fields[field].required = False
                
    def get_draft_application_id(self, obj):
        user = self.context['request'].user  # Получаем текущего пользователя
        if not user.is_authenticated:
            return None  # Если пользователь не аутентифицирован, возвращаем None
        draft_application = Application.objects.filter(user=user, status='draft', is_deleted=False).first()
        return draft_application.id if draft_application else None

class ApplicationServiceSerializer(serializers.ModelSerializer):
    service = serializers.PrimaryKeyRelatedField(queryset=Service.objects.all())
    application = serializers.PrimaryKeyRelatedField(queryset=Application.objects.all())

    class Meta:
        model = ApplicationService
        fields = '__all__'

class ApplicationSerializer(serializers.ModelSerializer):
    application_services = ApplicationServiceSerializer(many=True, read_only=True)

    class Meta:
        model = Application
        fields = '__all__'
    
    def create(self, validated_data):
        return super().create(validated_data)
        
    def __init__(self, *args, **kwargs):
        if kwargs.get('context') and kwargs['context'].get('request') and kwargs['context']['request'].method == 'POST':
            self.fields.pop('application_services', None)
        super().__init__(*args, **kwargs)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'