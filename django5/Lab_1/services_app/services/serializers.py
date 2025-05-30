from rest_framework import serializers
from .models import Service, Application, ApplicationService, User
from django.contrib.auth.hashers import make_password

class ServiceSerializer(serializers.ModelSerializer):
    draft_application_id = serializers.SerializerMethodField()

    class Meta:
        model = Service
        fields = ['id', 'name', 'description', 'image', 'is_deleted', 'draft_application_id']
        read_only_fields = ['is_deleted']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if self.context['request'].method in ['PUT', 'PATCH']:
            for field in self.fields:
                self.fields[field].required = False
                
    def get_draft_application_id(self, obj):
        user = self.context['request'].user
        if not user.is_authenticated:
            return None
        draft_application = Application.objects.filter(user=user, status='draft', is_deleted=False).first()
        return draft_application.id if draft_application else None

class ApplicationServiceSerializer(serializers.ModelSerializer):
    service = serializers.PrimaryKeyRelatedField(queryset=Service.objects.filter(is_deleted=False))
    application = serializers.PrimaryKeyRelatedField(queryset=Application.objects.filter(is_deleted=False))

    class Meta:
        model = ApplicationService
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class ApplicationSerializer(serializers.ModelSerializer):
    application_services = ApplicationServiceSerializer(many=True, read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    moderator = serializers.PrimaryKeyRelatedField(read_only=True, allow_null=True)

    class Meta:
        model = Application
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'user', 'moderator']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if self.context['request'].method == 'POST':
            self.fields.pop('application_services', None)
            self.fields.pop('status', None)
            self.fields.pop('moderator', None)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'email', 'is_staff']
        extra_kwargs = {
            'password': {'write_only': True},
            'is_staff': {'read_only': True}
        }

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)
    

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=False)

    class Meta:
        model = User
        fields = ['username', 'password', 'email']
        extra_kwargs = {
            'email': {'required': False}
        }

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data.get('email', '')
        )
        return user