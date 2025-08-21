from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User


class RegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    confirm_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'password', 'confirm_password')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True},
        }
    
    def validate(self, attrs):
        """Validate the registration data."""
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return attrs
    
    def validate_email(self, value):
        """Validate that email is unique."""
        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()
    
    def create(self, validated_data):
        """Create a new user."""
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    
    email = serializers.EmailField()
    password = serializers.CharField(
        style={'input_type': 'password'},
        write_only=True
    )
    
    def validate(self, attrs):
        """Validate login credentials."""
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            # Authenticate user
            user = authenticate(
                request=self.context.get('request'),
                email=email,
                password=password
            )
            
            if not user:
                raise serializers.ValidationError('Invalid email or password.')
            
            if not user.is_active:
                raise serializers.ValidationError('Account is not activated. Please check your email.')
            
            attrs['user'] = user
        else:
            raise serializers.ValidationError('Must include email and password.')
        
        return attrs


class ActivationSerializer(serializers.Serializer):
    """Serializer for account activation."""
    
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6, min_length=6)
    
    def validate_email(self, value):
        """Validate that user exists."""
        try:
            user = User.objects.get(email=value.lower())
            if user.is_active:
                raise serializers.ValidationError("Account is already activated.")
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")
        return value.lower()


class ProfileViewSerializer(serializers.ModelSerializer):
    """Serializer for viewing user profile."""
    
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email', 'full_name', 
                 'is_active', 'date_joined', 'created_at', 'updated_at', 'is_staff')
        read_only_fields = ('id', 'email', 'is_active', 'date_joined', 'created_at', 'updated_at', 'is_staff')


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile."""
    
    class Meta:
        model = User
        fields = ('first_name', 'last_name')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
        }
    
    def validate_first_name(self, value):
        """Validate first name."""
        if not value.strip():
            raise serializers.ValidationError("First name cannot be empty.")
        return value.strip()
    
    def validate_last_name(self, value):
        """Validate last name."""
        if not value.strip():
            raise serializers.ValidationError("Last name cannot be empty.")
        return value.strip()


class ForgotPasswordSerializer(serializers.Serializer):
    """Serializer for forgot password request."""
    
    email = serializers.EmailField()
    
    def validate_email(self, value):
        """Validate that user exists and is active."""
        try:
            user = User.objects.get(email=value.lower())
            if not user.is_active:
                raise serializers.ValidationError("Account is not activated.")
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")
        return value.lower()


class ResetPasswordSerializer(serializers.Serializer):
    """Serializer for password reset."""
    
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6, min_length=6)
    new_password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    confirm_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        """Validate the password reset data."""
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return attrs
    
    def validate_email(self, value):
        """Validate that user exists and is active."""
        try:
            user = User.objects.get(email=value.lower())
            if not user.is_active:
                raise serializers.ValidationError("Account is not activated.")
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")
        return value.lower()
