from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Transaction, TransactionStatus, CurrencyChoices

User = get_user_model()


class TransactionCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new transactions.
    Used when users initiate transactions with receiver details and payment proof.
    """
    
    class Meta:
        model = Transaction
        fields = [
            # Transaction details
            'amount',
            'currency',
            'description',
            
            # User payment details
            'user_payment_method',
            'user_bank_name',
            'user_account_name',
            'user_account_number',
            'user_payment_reference',
            'user_payment_slip',
            
            # Receiver details
            'receiver_account_name',
            'receiver_account_number',
            'receiver_swift_code',
            'receiver_barcode_image',
        ]
    
    def validate_amount(self, value):
        """Validate transaction amount is positive."""
        if value <= 0:
            raise serializers.ValidationError("Transaction amount must be greater than zero.")
        return value
    
    def validate_receiver_swift_code(self, value):
        """Validate SWIFT code format."""
        if value and len(value) not in [8, 11]:
            raise serializers.ValidationError("SWIFT code must be 8 or 11 characters long.")
        return value.upper() if value else value
    
    def validate(self, attrs):
        """Cross-field validation."""
        # If user provides payment details, ensure they're complete
        user_payment_fields = [
            'user_payment_method', 'user_bank_name', 
            'user_account_name', 'user_account_number'
        ]
        
        provided_fields = [field for field in user_payment_fields if attrs.get(field)]
        
        if provided_fields and len(provided_fields) < len(user_payment_fields):
            missing_fields = [field for field in user_payment_fields if not attrs.get(field)]
            raise serializers.ValidationError({
                'user_payment_details': f"If providing payment details, all fields are required. Missing: {', '.join(missing_fields)}"
            })
        
        return attrs
    
    def create(self, validated_data):
        """Create transaction with authenticated user and pending status."""
        # Set the user from the request context
        validated_data['user'] = self.context['request'].user
        
        # Ensure status is pending
        validated_data['status'] = TransactionStatus.PENDING
        
        return super().create(validated_data)


class TransactionListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing user's transactions.
    Shows basic transaction information without sensitive admin fields.
    """
    user_email = serializers.EmailField(source='user.email', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    currency_display = serializers.CharField(source='get_currency_display', read_only=True)
    
    # File URLs for frontend display
    user_payment_slip_url = serializers.SerializerMethodField()
    receiver_barcode_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Transaction
        fields = [
            'id',
            'reference_number',
            'user_email',
            'status',
            'status_display',
            'amount',
            'currency',
            'currency_display',
            'description',
            'receiver_account_name',
            'receiver_account_number',
            'receiver_swift_code',
            'user_payment_method',
            'user_bank_name',
            'user_payment_reference',
            'user_payment_slip_url',
            'receiver_barcode_image_url',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id', 'reference_number', 'user_email', 'status', 
            'status_display', 'created_at', 'updated_at'
        ]
    
    def get_user_payment_slip_url(self, obj):
        """Get user payment slip URL."""
        if obj.user_payment_slip:
            return obj.user_payment_slip.url
        return None
    
    def get_receiver_barcode_image_url(self, obj):
        """Get receiver barcode image URL."""
        if obj.receiver_barcode_image:
            return obj.receiver_barcode_image.url
        return None


class TransactionDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for detailed transaction view.
    Shows all transaction information for the user.
    """
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_full_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    currency_display = serializers.CharField(source='get_currency_display', read_only=True)
    
    # File information
    supporting_documents = serializers.SerializerMethodField()
    
    class Meta:
        model = Transaction
        fields = [
            'id',
            'reference_number',
            'user_email',
            'user_full_name',
            'status',
            'status_display',
            'amount',
            'currency',
            'currency_display',
            'description',
            
            # User payment details
            'user_payment_method',
            'user_bank_name',
            'user_account_name',
            'user_account_number',
            'user_payment_reference',
            
            # Receiver details
            'receiver_account_name',
            'receiver_account_number',
            'receiver_swift_code',
            
            # File information
            'supporting_documents',
            
            # Metadata
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id', 'reference_number', 'user_email', 'user_full_name',
            'status', 'status_display', 'supporting_documents',
            'created_at', 'updated_at'
        ]
    
    def get_user_full_name(self, obj):
        """Get user's full name."""
        if hasattr(obj.user, 'first_name') and hasattr(obj.user, 'last_name'):
            return f"{obj.user.first_name} {obj.user.last_name}".strip()
        return obj.user.email
    
    def get_supporting_documents(self, obj):
        """Get all supporting documents with their URLs."""
        return obj.supporting_documents


class TransactionUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating transaction details.
    Users can only update pending transactions and only specific fields.
    """
    
    class Meta:
        model = Transaction
        fields = [
            'description',
            'user_payment_method',
            'user_bank_name',
            'user_account_name',
            'user_account_number',
            'user_payment_reference',
            'user_payment_slip',
            'receiver_account_name',
            'receiver_account_number',
            'receiver_swift_code',
            'receiver_barcode_image',
        ]
    
    def validate(self, attrs):
        """Only allow updates on pending transactions."""
        instance = self.instance
        if instance and instance.status != TransactionStatus.PENDING:
            raise serializers.ValidationError(
                "Cannot update transaction that is not in pending status."
            )
    def validate_receiver_swift_code(self, value):
        """Validate SWIFT code format."""
        if value and len(value) not in [8, 11]:
            raise serializers.ValidationError("SWIFT code must be 8 or 11 characters long.")
        return value.upper() if value else value


# Admin Serializers
class AdminTransactionListSerializer(serializers.ModelSerializer):
    """
    Serializer for admin transaction listing.
    Shows basic info with user details and transaction ID only.
    """
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_full_name = serializers.SerializerMethodField()
    user_id = serializers.CharField(source='user.id', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    currency_display = serializers.CharField(source='get_currency_display', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id',
            'reference_number',
            'user_id',
            'user_email',
            'user_full_name',
            'status',
            'status_display',
            'amount',
            'currency',
            'currency_display',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id', 'reference_number', 'user_id', 'user_email', 'user_full_name',
            'status', 'status_display', 'amount', 'currency', 'currency_display',
            'created_at', 'updated_at'
        ]
    
    def get_user_full_name(self, obj):
        """Get user's full name."""
        if hasattr(obj.user, 'first_name') and hasattr(obj.user, 'last_name'):
            full_name = f"{obj.user.first_name} {obj.user.last_name}".strip()
            return full_name if full_name else obj.user.email
        return obj.user.email


class AdminTransactionDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for admin transaction details.
    Shows complete transaction information including user details.
    """
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_full_name = serializers.SerializerMethodField()
    user_id = serializers.CharField(source='user.id', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    currency_display = serializers.CharField(source='get_currency_display', read_only=True)
    
    # Processing admin info
    processing_admin_email = serializers.SerializerMethodField()
    processing_admin_id = serializers.SerializerMethodField()
    
    # File information
    supporting_documents = serializers.SerializerMethodField()
    
    class Meta:
        model = Transaction
        fields = [
            'id',
            'reference_number',
            'user_id',
            'user_email',
            'user_full_name',
            'status',
            'status_display',
            'amount',
            'currency',
            'currency_display',
            'description',
            
            # User payment details
            'user_payment_method',
            'user_bank_name',
            'user_account_name',
            'user_account_number',
            'user_payment_reference',
            
            # Receiver details
            'receiver_account_name',
            'receiver_account_number',
            'receiver_swift_code',
            
            # Processing admin info
            'processing_admin_email',
            'processing_admin_id',
            
            # File information
            'supporting_documents',
            
            # Internal notes
            'notes',
            
            # Metadata
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id', 'reference_number', 'user_id', 'user_email', 'user_full_name',
            'status', 'status_display', 'amount', 'currency', 'currency_display',
            'description', 'user_payment_method', 'user_bank_name', 'user_account_name',
            'user_account_number', 'user_payment_reference', 'receiver_account_name',
            'receiver_account_number', 'receiver_swift_code', 'processing_admin_email',
            'processing_admin_id', 'supporting_documents', 'notes', 'created_at', 'updated_at'
        ]
    
    def get_user_full_name(self, obj):
        """Get user's full name."""
        if hasattr(obj.user, 'first_name') and hasattr(obj.user, 'last_name'):
            full_name = f"{obj.user.first_name} {obj.user.last_name}".strip()
            return full_name if full_name else obj.user.email
        return obj.user.email
    
    def get_processing_admin_email(self, obj):
        """Get processing admin email if exists."""
        if obj.processing_admin:
            return obj.processing_admin.email
        return None
    
    def get_processing_admin_id(self, obj):
        """Get processing admin ID if exists."""
        if obj.processing_admin:
            return obj.processing_admin.id
        return None
    
    def get_supporting_documents(self, obj):
        """Get all supporting documents with their URLs."""
        return obj.supporting_documents


class AdminTransactionUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for admin transaction updates.
    Allows admins to update transaction status and add completion documents.
    """
    
    class Meta:
        model = Transaction
        fields = [
            'status',
            'transaction_completion_document',
            'additional_completion_document',
            'notes'
        ]
    
    def validate_status(self, value):
        """Validate status transitions."""
        instance = self.instance
        if not instance:
            return value
            
        # Define valid status transitions for admin
        valid_transitions = {
            TransactionStatus.PENDING: [TransactionStatus.PROCESSING, TransactionStatus.FAILED, TransactionStatus.CANCELLED],
            TransactionStatus.PROCESSING: [TransactionStatus.COMPLETED, TransactionStatus.FAILED],
            # Completed, failed, and cancelled transactions cannot be changed
        }
        
        current_status = instance.status
        if current_status not in valid_transitions:
            raise serializers.ValidationError(f"Cannot change status from {current_status}")
            
        if value not in valid_transitions[current_status]:
            raise serializers.ValidationError(
                f"Invalid status transition from {current_status} to {value}"
            )
        
        return value
    
    def validate(self, attrs):
        """Cross-field validation for completion."""
        status_value = attrs.get('status', self.instance.status if self.instance else None)
        
        # If marking as completed, ensure completion documents are provided
        if status_value == TransactionStatus.COMPLETED:
            if not attrs.get('transaction_completion_document') and not getattr(self.instance, 'transaction_completion_document', None):
                raise serializers.ValidationError({
                    'transaction_completion_document': 'Completion document is required when marking transaction as completed.'
                })
        
        return attrs
