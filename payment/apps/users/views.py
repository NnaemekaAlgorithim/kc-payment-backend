from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.openapi import OpenApiTypes
import logging

from .models import User
from .serializers import (
    RegistrationSerializer,
    LoginSerializer,
    ActivationSerializer,
    ProfileViewSerializer,
    ProfileUpdateSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer
)
from .utils import OTPManager, EmailService

logger = logging.getLogger(__name__)


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user management operations including registration, login, 
    activation, profile management, and password reset functionality.
    """
    queryset = User.objects.all()
    serializer_class = ProfileViewSerializer
    otp_manager = OTPManager()
    email_service = EmailService()
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['register', 'activate', 'login', 'forgot_password', 'reset_password']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        """
        Return the class to use for the serializer based on the action.
        """
        if self.action == 'register':
            return RegistrationSerializer
        elif self.action == 'login':
            return LoginSerializer
        elif self.action == 'activate':
            return ActivationSerializer
        elif self.action == 'update_profile':
            return ProfileUpdateSerializer
        elif self.action == 'forgot_password':
            return ForgotPasswordSerializer
        elif self.action == 'reset_password':
            return ResetPasswordSerializer
        return ProfileViewSerializer
    
    @extend_schema(
        summary="Register new user",
        description="Register a new user account. Sends activation email with OTP code.",
        responses={
            201: {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "message": {"type": "string"},
                    "data": {
                        "type": "object",
                        "properties": {
                            "user_id": {"type": "string"},
                            "email": {"type": "string"},
                            "full_name": {"type": "string"}
                        }
                    }
                }
            },
            400: {"description": "Validation errors"}
        },
        tags=["Authentication"]
    )
    @action(detail=False, methods=['post'])
    def register(self, request):
        """
        Register a new user account.
        
        This endpoint creates a new user account and sends an activation email
        with an OTP code. The user must activate their account before logging in.
        """
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            try:
                user = serializer.save()
                
                # Generate OTP for email activation
                otp = self.otp_manager.generate_otp()
                self.otp_manager.store_otp(user.email, otp, 'activation')
                
                # Send activation email
                self.email_service.send_activation_email(user, otp)
                
                logger.info(f"User registered successfully: {user.email}")
                
                return Response({
                    'success': True,
                    'message': 'Registration successful. Please check your email for activation instructions.',
                    'data': {
                        'user_id': str(user.id),
                        'email': user.email,
                        'full_name': f"{user.first_name} {user.last_name}".strip()
                    }
                }, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                logger.error(f"Registration error: {str(e)}")
                return Response({
                    'success': False,
                    'message': 'Registration failed. Please try again later.',
                    'errors': {'general': ['An unexpected error occurred.']}
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'success': False,
            'message': 'Registration failed due to validation errors.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        summary="Activate user account",
        description="""
        Activate a user account using the OTP code sent via email. Returns JWT tokens upon successful activation.
        
        **Two modes of operation:**
        1. **Activation mode** (resend=false): Verify OTP and activate account
        2. **Resend mode** (resend=true): Send a new OTP to user's email
        """,
        responses={
            200: {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "message": {"type": "string"},
                    "data": {
                        "type": "object",
                        "properties": {
                            "access_token": {"type": "string"},
                            "refresh_token": {"type": "string"},
                            "user": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string"},
                                    "email": {"type": "string"},
                                    "first_name": {"type": "string"},
                                    "last_name": {"type": "string"},
                                    "full_name": {"type": "string"},
                                    "is_active": {"type": "boolean"},
                                    "is_staff": {"type": "boolean"}
                                }
                            }
                        }
                    }
                }
            },
            400: {"description": "Invalid OTP or validation errors"}
        },
        tags=["Authentication"]
    )
    @action(detail=False, methods=['post'])
    def activate(self, request):
        """
        Activate a user account using OTP or resend a new OTP.
        
        This endpoint has two modes:
        1. Activation: Verify OTP and activate account (resend=false)
        2. Resend: Send new OTP to user's email (resend=true)
        """
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp = serializer.validated_data.get('otp')
            resend = serializer.validated_data.get('resend', False)
            
            try:
                user = User.objects.get(email=email)
                
                if user.is_active:
                    return Response({
                        'success': False,
                        'message': 'Account is already activated.',
                        'errors': {'general': ['Account is already active.']}
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Handle resend OTP request
                if resend:
                    try:
                        # Generate new OTP for email activation
                        new_otp = self.otp_manager.generate_otp()
                        self.otp_manager.store_otp(user.email, new_otp, 'activation')
                        
                        # Send activation email with new OTP
                        self.email_service.send_activation_email(user, new_otp)
                        
                        logger.info(f"New activation OTP sent to: {user.email}")
                        
                        return Response({
                            'success': True,
                            'message': 'New activation code has been sent to your email.',
                            'data': {
                                'email': user.email,
                                'resent': True
                            }
                        }, status=status.HTTP_200_OK)
                        
                    except Exception as e:
                        logger.error(f"OTP resend error: {str(e)}")
                        return Response({
                            'success': False,
                            'message': 'Failed to send activation code. Please try again later.',
                            'errors': {'general': ['An error occurred while sending the activation code.']}
                        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
                # Handle account activation
                else:
                    # Verify OTP
                    if self.otp_manager.verify_otp(email, otp, 'activation'):
                        user.is_active = True
                        user.save()
                        
                        # Generate JWT tokens
                        refresh = RefreshToken.for_user(user)
                        access_token = refresh.access_token
                        
                        # Update last login since user is now activated and logged in
                        user.last_login = timezone.now()
                        user.save(update_fields=['last_login'])
                        
                        # Send welcome email
                        self.email_service.send_welcome_email(user)
                        
                        logger.info(f"User activated successfully: {user.email}")
                        
                        return Response({
                            'success': True,
                            'message': 'Account activated successfully. You are now logged in.',
                            'data': {
                                'access_token': str(access_token),
                                'refresh_token': str(refresh),
                                'user': {
                                    'id': str(user.id),
                                    'email': user.email,
                                    'first_name': user.first_name,
                                    'last_name': user.last_name,
                                    'full_name': f"{user.first_name} {user.last_name}".strip(),
                                    'is_active': user.is_active,
                                    'is_staff': user.is_staff
                                }
                            }
                        }, status=status.HTTP_200_OK)
                    else:
                        return Response({
                            'success': False,
                            'message': 'Invalid or expired OTP code.',
                            'errors': {'otp': ['Invalid or expired OTP code.']}
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
            except User.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'User not found.',
                    'errors': {'email': ['No account found with this email address.']}
                }, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                logger.error(f"Activation error: {str(e)}")
                return Response({
                    'success': False,
                    'message': 'Activation failed. Please try again later.',
                    'errors': {'general': ['An unexpected error occurred.']}
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'success': False,
            'message': 'Activation failed due to validation errors.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        summary="User login",
        description="Authenticate user and return JWT tokens.",
        responses={
            200: {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "message": {"type": "string"},
                    "data": {
                        "type": "object",
                        "properties": {
                            "access_token": {"type": "string"},
                            "refresh_token": {"type": "string"},
                            "user": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string"},
                                    "email": {"type": "string"},
                                    "first_name": {"type": "string"},
                                    "last_name": {"type": "string"},
                                    "is_active": {"type": "boolean"},
                                    "is_staff": {"type": "boolean"}
                                }
                            }
                        }
                    }
                }
            },
            400: {"description": "Invalid credentials or validation errors"}
        },
        tags=["Authentication"]
    )
    @action(detail=False, methods=['post'])
    def login(self, request):
        """
        Authenticate user and return JWT tokens.
        
        This endpoint authenticates a user using email and password,
        and returns access and refresh JWT tokens.
        """
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            
            try:
                user = authenticate(request, username=email, password=password)
                
                if user:
                    if not user.is_active:
                        return Response({
                            'success': False,
                            'message': 'Account is not activated. Please check your email for activation instructions.',
                            'errors': {'general': ['Account is not activated.']}
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    # Generate JWT tokens
                    refresh = RefreshToken.for_user(user)
                    access_token = refresh.access_token
                    
                    # Update last login
                    user.last_login = timezone.now()
                    user.save(update_fields=['last_login'])
                    
                    logger.info(f"User logged in successfully: {user.email}")
                    
                    return Response({
                        'success': True,
                        'message': 'Login successful.',
                        'data': {
                            'access_token': str(access_token),
                            'refresh_token': str(refresh),
                            'user': {
                                'id': str(user.id),
                                'email': user.email,
                                'first_name': user.first_name,
                                'last_name': user.last_name,
                                'is_active': user.is_active,
                                'is_staff': user.is_staff
                            }
                        }
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'success': False,
                        'message': 'Invalid email or password.',
                        'errors': {'general': ['Invalid email or password.']}
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except Exception as e:
                logger.error(f"Login error: {str(e)}")
                return Response({
                    'success': False,
                    'message': 'Login failed. Please try again later.',
                    'errors': {'general': ['An unexpected error occurred.']}
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'success': False,
            'message': 'Login failed due to validation errors.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        summary="Get user profile",
        description="Retrieve the authenticated user's profile information.",
        responses={
            200: ProfileViewSerializer,
            401: {"description": "Authentication required"}
        },
        tags=["Profile"]
    )
    @method_decorator(cache_page(60 * 5))  # Cache for 5 minutes
    @action(detail=False, methods=['get'])
    def profile(self, request):
        """
        Retrieve the authenticated user's profile.
        
        This endpoint returns the profile information of the authenticated user.
        """
        serializer = self.get_serializer(request.user)
        return Response({
            'success': True,
            'message': 'Profile retrieved successfully.',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    @extend_schema(
        summary="Update user profile",
        description="Update the authenticated user's profile information.",
        responses={
            200: ProfileUpdateSerializer,
            400: {"description": "Validation errors"},
            401: {"description": "Authentication required"}
        },
        tags=["Profile"]
    )
    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        """
        Update the authenticated user's profile.
        
        This endpoint allows the authenticated user to update their
        profile information such as first name and last name.
        """
        serializer = self.get_serializer(
            request.user, 
            data=request.data, 
            partial=request.method == 'PATCH'
        )
        
        if serializer.is_valid():
            try:
                user = serializer.save()
                
                logger.info(f"Profile updated successfully: {user.email}")
                
                return Response({
                    'success': True,
                    'message': 'Profile updated successfully.',
                    'data': ProfileViewSerializer(user).data
                }, status=status.HTTP_200_OK)
                
            except Exception as e:
                logger.error(f"Profile update error: {str(e)}")
                return Response({
                    'success': False,
                    'message': 'Profile update failed. Please try again later.',
                    'errors': {'general': ['An unexpected error occurred.']}
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'success': False,
            'message': 'Profile update failed due to validation errors.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        summary="Request password reset",
        description="Send password reset OTP to user's email address.",
        responses={
            200: {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "message": {"type": "string"}
                }
            },
            400: {"description": "Validation errors"}
        },
        tags=["Password Reset"]
    )
    @action(detail=False, methods=['post'])
    def forgot_password(self, request):
        """
        Request password reset.
        
        This endpoint sends a password reset OTP to the user's email address
        if the email exists in the system.
        """
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            try:
                user = User.objects.get(email=email, is_active=True)
                
                # Generate OTP for password reset
                otp = self.otp_manager.generate_otp()
                self.otp_manager.store_otp(email, otp, 'password_reset')
                
                # Send password reset email
                self.email_service.send_password_reset_email(user, otp)
                
                logger.info(f"Password reset requested for: {email}")
                
                return Response({
                    'success': True,
                    'message': 'Password reset instructions have been sent to your email.'
                }, status=status.HTTP_200_OK)
                
            except User.DoesNotExist:
                # For security reasons, we don't reveal if the email exists
                return Response({
                    'success': True,
                    'message': 'Password reset instructions have been sent to your email.'
                }, status=status.HTTP_200_OK)
            except Exception as e:
                logger.error(f"Forgot password error: {str(e)}")
                return Response({
                    'success': False,
                    'message': 'Password reset request failed. Please try again later.',
                    'errors': {'general': ['An unexpected error occurred.']}
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'success': False,
            'message': 'Password reset request failed due to validation errors.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        summary="Reset password",
        description="Reset user password using OTP code.",
        responses={
            200: {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "message": {"type": "string"}
                }
            },
            400: {"description": "Invalid OTP or validation errors"}
        },
        tags=["Password Reset"]
    )
    @action(detail=False, methods=['post'])
    def reset_password(self, request):
        """
        Reset user password using OTP.
        
        This endpoint resets the user's password after verifying the OTP
        sent to their email during the forgot password process.
        """
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp = serializer.validated_data['otp']
            new_password = serializer.validated_data['new_password']
            
            try:
                user = User.objects.get(email=email, is_active=True)
                
                # Verify OTP
                if self.otp_manager.verify_otp(email, otp, 'password_reset'):
                    user.set_password(new_password)
                    user.save()
                    
                    logger.info(f"Password reset successfully for: {email}")
                    
                    return Response({
                        'success': True,
                        'message': 'Password reset successfully. You can now log in with your new password.'
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'success': False,
                        'message': 'Invalid or expired OTP code.',
                        'errors': {'otp': ['Invalid or expired OTP code.']}
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except User.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'User not found.',
                    'errors': {'email': ['No active account found with this email address.']}
                }, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                logger.error(f"Password reset error: {str(e)}")
                return Response({
                    'success': False,
                    'message': 'Password reset failed. Please try again later.',
                    'errors': {'general': ['An unexpected error occurred.']}
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'success': False,
            'message': 'Password reset failed due to validation errors.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
