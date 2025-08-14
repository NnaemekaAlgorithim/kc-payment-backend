from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.openapi import OpenApiTypes
import logging

from .models import Transaction, TransactionStatus
from .serializers import (
    TransactionCreateSerializer,
    TransactionListSerializer,
    TransactionDetailSerializer,
    TransactionUpdateSerializer,
    AdminTransactionListSerializer,
    AdminTransactionDetailSerializer,
    AdminTransactionUpdateSerializer,
)
from payment.apps.common.permissions import IsAdminOrReadOnly

logger = logging.getLogger(__name__)


class TransactionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling user transactions.
    
    This viewset provides comprehensive transaction management functionality
    for authenticated users including creating, updating, and tracking transactions.
    
    Users can:
    - Create new transactions with payment details and file uploads
    - List their own transactions with filtering and search
    - Retrieve detailed transaction information
    - Update pending transactions only
    - Cancel pending transactions
    - Access transaction statistics and documents
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ['status', 'currency']
    ordering_fields = ['created_at', 'updated_at', 'amount']
    ordering = ['-created_at']
    search_fields = ['reference_number', 'receiver_account_name', 'description']
    
    def get_queryset(self):
        """Return transactions for the authenticated user only."""
        return Transaction.objects.filter(user=self.request.user)
    
    def retrieve(self, request, *args, **kwargs):
        """
        Override retrieve to redirect to list with transaction_id parameter.
        This ensures we use a single endpoint for both list and detail views.
        """
        transaction_id = kwargs.get('pk')
        # Redirect to list view with transaction_id parameter
        request.query_params._mutable = True
        request.query_params['transaction_id'] = transaction_id
        request.query_params._mutable = False
        return self.list(request)
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return TransactionCreateSerializer
        elif self.action == 'list':
            return TransactionListSerializer
        elif self.action == 'retrieve':
            return TransactionDetailSerializer
        elif self.action in ['update', 'partial_update']:
            return TransactionUpdateSerializer
        return TransactionDetailSerializer
    
    @extend_schema(
        summary="Create new transaction",
        description="""
        Create a new payment transaction with status set to PENDING.
        
        **Content-Type: multipart/form-data** (for file uploads)
        
        This endpoint allows authenticated users to initiate a new transaction by providing:
        
        **Required Fields:**
        - `amount`: Transaction amount (decimal, e.g., "1000.00")
        - `currency`: Currency code (e.g., "USD", "EUR", "GBP")
        - `receiver_account_name`: Receiver's account holder name
        - `receiver_account_number`: Receiver's account number
        - `receiver_swift_code`: Receiver's bank SWIFT/BIC code
        
        **Optional User Payment Details:**
        - `user_payment_method`: Payment method (e.g., "Bank Transfer")
        - `user_bank_name`: User's bank name
        - `user_account_name`: User's account holder name  
        - `user_account_number`: User's account number
        - `user_payment_reference`: Payment reference from user's bank
        - `description`: Transaction description or memo
        
        **File Uploads (multipart/form-data):**
        - `user_payment_slip`: Payment receipt/slip (PDF, JPG, PNG - max 10MB)
        - `receiver_barcode_image`: Receiver's barcode image (JPG, PNG - max 5MB)
        
        **File Upload Requirements:**
        - Supported formats: PDF, JPG, JPEG, PNG, GIF
        - Payment slip max size: 10MB
        - Barcode image max size: 5MB
        - Files are stored in Google Cloud Platform (GCP) Cloud Storage
        
        **Example using cURL:**
        ```bash
        curl -X POST http://localhost:8000/api/transactions/ \\
          -H "Authorization: Bearer YOUR_JWT_TOKEN" \\
          -F "amount=1000.00" \\
          -F "currency=USD" \\
          -F "receiver_account_name=John Doe Business" \\
          -F "receiver_account_number=1234567890" \\
          -F "receiver_swift_code=CHASUS33XXX" \\
          -F "description=Payment for services" \\
          -F "user_payment_method=Bank Transfer" \\
          -F "user_bank_name=Wells Fargo" \\
          -F "user_account_name=Jane Smith" \\
          -F "user_account_number=9876543210" \\
          -F "user_payment_reference=WF123456789" \\
          -F "user_payment_slip=@/path/to/payment-receipt.pdf" \\
          -F "receiver_barcode_image=@/path/to/barcode.jpg"
        ```
        
        All file uploads are stored securely in Google Cloud Platform Cloud Storage.
        The transaction will be created with PENDING status and can be updated until processed by an admin.
        """,
        request=TransactionCreateSerializer,
        responses={
            201: {
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                    "transaction": {"type": "object", "description": "Created transaction details"}
                }
            },
            400: {"description": "Validation errors"},
            401: {"description": "Authentication required"}
        },
        examples=[
            OpenApiExample(
                'Create Transaction with Files',
                summary='Example transaction creation with file uploads',
                description='Sample multipart/form-data request for creating a transaction with file uploads',
                value={
                    "amount": "1000.00",
                    "currency": "USD",
                    "description": "Payment for services rendered",
                    "user_payment_method": "Bank Transfer",
                    "user_bank_name": "Chase Bank",
                    "user_account_name": "John Doe",
                    "user_account_number": "1234567890",
                    "user_payment_reference": "TXN123456789",
                    "receiver_account_name": "Jane Smith Business",
                    "receiver_account_number": "9876543210",
                    "receiver_swift_code": "CHASUS33XXX",
                    # Files should be uploaded as multipart/form-data:
                    # user_payment_slip: <file upload - PDF/Image of payment receipt>
                    # receiver_barcode_image: <file upload - PNG/JPG of receiver's barcode>
                },
                request_only=True
            ),
            OpenApiExample(
                'Minimal Transaction',
                summary='Minimal required fields',
                description='Minimum required fields to create a transaction',
                value={
                    "amount": "500.00",
                    "currency": "USD",
                    "receiver_account_name": "ABC Company Ltd",
                    "receiver_account_number": "1122334455",
                    "receiver_swift_code": "ABCDUS33"
                },
                request_only=True
            ),
        ],
        tags=["Transactions"]
    )
    def create(self, request, *args, **kwargs):
        """
        Create a new transaction.
        Sets status to PENDING and associates with authenticated user.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Create the transaction
            transaction = serializer.save()
            
            # Return detailed response
            response_serializer = TransactionDetailSerializer(
                transaction, context={'request': request}
            )
            
            logger.info(f"Transaction created successfully: {transaction.reference_number} by {request.user.email}")
            
            return Response(
                {
                    'message': 'Transaction created successfully',
                    'transaction': response_serializer.data
                },
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            logger.error(f"Transaction creation error: {str(e)}")
            return Response(
                {'error': 'Transaction creation failed. Please try again later.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="List user transactions or get specific transaction",
        description="""
        Retrieve transactions for the authenticated user with comprehensive filtering options.
        
        **Get specific transaction by ID:**
        - Add `?transaction_id=123` to get details of a specific transaction
        - Returns detailed transaction information if transaction_id is provided
        
        **Filter transactions:**
        - Filter by status: pending, processing, completed, failed, cancelled
        - Filter by currency: USD, EUR, GBP, etc.
        - Search in: reference number, receiver account name, description
        - Order by: created_at, updated_at, amount (use - prefix for descending)
        
        **Status filtering examples:**
        - `?status=pending` - Get all pending transactions
        - `?status=completed` - Get all completed transactions  
        - `?status=cancelled` - Get all cancelled transactions
        - `?status=processing` - Get all processing transactions
        - `?status=failed` - Get all failed transactions
        """,
        parameters=[
            OpenApiParameter(
                name='transaction_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Get specific transaction by ID (returns detailed view)',
                required=False
            ),
            OpenApiParameter(
                name='status',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by transaction status',
                enum=['pending', 'processing', 'completed', 'failed', 'cancelled'],
                required=False
            ),
            OpenApiParameter(
                name='currency',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by currency code (e.g., USD, EUR, GBP)',
                required=False
            ),
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Search in reference number, receiver name, description',
                required=False
            ),
            OpenApiParameter(
                name='ordering',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Order results by field (use - for descending)',
                enum=['created_at', '-created_at', 'updated_at', '-updated_at', 'amount', '-amount'],
                required=False
            ),
        ],
        responses={
            200: {
                "description": "List of transactions or single transaction details. Returns list for general queries, single object when transaction_id is provided."
            },
            401: {"description": "Authentication required"},
            404: {"description": "Transaction not found (when using transaction_id)"}
        },
        examples=[
            OpenApiExample(
                'List All Transactions',
                summary='Get all user transactions',
                description='Returns paginated list of all transactions',
                value="GET /api/transactions/"
            ),
            OpenApiExample(
                'Get Specific Transaction',
                summary='Get transaction by ID',
                description='Returns detailed view of specific transaction',
                value="GET /api/transactions/?transaction_id=123"
            ),
            OpenApiExample(
                'Filter by Status',
                summary='Get pending transactions',
                description='Returns all pending transactions',
                value="GET /api/transactions/?status=pending"
            ),
        ],
        tags=["Transactions"]
    )
    def list(self, request, *args, **kwargs):
        """List all transactions for the authenticated user or get specific transaction by ID."""
        # Check if transaction_id is provided in query params
        transaction_id = request.query_params.get('transaction_id')
        
        if transaction_id:
            try:
                # Get specific transaction by ID
                transaction = self.get_queryset().get(id=transaction_id)
                serializer = TransactionDetailSerializer(transaction, context={'request': request})
                return Response(serializer.data)
            except Transaction.DoesNotExist:
                return Response(
                    {'error': 'Transaction not found or you do not have permission to access it.'},
                    status=status.HTTP_404_NOT_FOUND
                )
            except ValueError:
                return Response(
                    {'error': 'Invalid transaction ID format.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Default list behavior with filtering
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        summary="Update transaction",
        description="""
        Update transaction details. Only allowed for transactions in PENDING status.
        
        Users can update:
        - Transaction description
        - User payment details (method, bank info, payment reference)
        - Receiver account information
        - Upload new documents (replaces existing ones)
        
        Once a transaction is being processed by admin, it cannot be updated.
        """,
        request=TransactionUpdateSerializer,
        responses={
            200: {
                "type": "object", 
                "properties": {
                    "message": {"type": "string"},
                    "transaction": {"type": "object", "description": "Updated transaction details"}
                }
            },
            400: {"description": "Cannot update non-pending transaction or validation errors"},
            401: {"description": "Authentication required"},
            404: {"description": "Transaction not found"}
        },
        tags=["Transactions"]
    )
    def update(self, request, *args, **kwargs):
        """Update transaction (only allowed for pending transactions)."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # STRICT CHECK: Only allow updates on PENDING transactions
        if instance.status != TransactionStatus.PENDING:
            return Response(
                {
                    'error': 'Cannot update transaction that is not in pending status.',
                    'current_status': instance.status,
                    'message': 'Only pending transactions can be modified. This transaction is currently in processing or has been completed.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        try:
            transaction = serializer.save()
            
            # Return updated transaction details
            response_serializer = TransactionDetailSerializer(
                transaction, context={'request': request}
            )
            
            logger.info(f"Transaction updated successfully: {transaction.reference_number} by {request.user.email}")
            
            return Response(
                {
                    'message': 'Transaction updated successfully',
                    'transaction': response_serializer.data
                }
            )
        except Exception as e:
            logger.error(f"Transaction update error: {str(e)}")
            return Response(
                {'error': 'Transaction update failed. Please try again later.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Cancel transaction",
        description="""
        Cancel a pending transaction by setting its status to CANCELLED.
        
        Only transactions in PENDING status can be cancelled.
        Once cancelled, transactions cannot be updated or processed.
        
        This action is irreversible - use with caution.
        """,
        responses={
            200: {
                "type": "object",
                "properties": {
                    "message": {"type": "string"}
                }
            },
            400: {"description": "Cannot cancel non-pending transaction"},
            401: {"description": "Authentication required"},
            404: {"description": "Transaction not found"}
        },
        tags=["Transactions"]
    )
    def destroy(self, request, *args, **kwargs):
        """Cancel/delete transaction (only allowed for pending transactions)."""
        instance = self.get_object()
        
        if instance.status != TransactionStatus.PENDING:
            return Response(
                {'error': 'Cannot cancel transaction that is not in pending status.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Mark as cancelled instead of deleting
            instance.status = TransactionStatus.CANCELLED
            instance.save()
            
            logger.info(f"Transaction cancelled successfully: {instance.reference_number} by {request.user.email}")
            
            return Response(
                {'message': 'Transaction cancelled successfully'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Transaction cancellation error: {str(e)}")
            return Response(
                {'error': 'Transaction cancellation failed. Please try again later.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Cancel transaction (alternative method)",
        description="""
        Alternative method to cancel a pending transaction using POST request.
        
        This is an alternative to the DELETE method for cancelling transactions.
        Only transactions in PENDING status can be cancelled.
        """,
        responses={
            200: {
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                    "transaction": {"type": "object", "description": "Cancelled transaction details"}
                }
            },
            400: {"description": "Cannot cancel non-pending transaction"},
            401: {"description": "Authentication required"},
            404: {"description": "Transaction not found"}
        },
        tags=["Transactions"]
    )
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Custom action to cancel a pending transaction.
        Alternative to DELETE method.
        """
        transaction = self.get_object()
        
        if transaction.status != TransactionStatus.PENDING:
            return Response(
                {'error': 'Cannot cancel transaction that is not in pending status.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            transaction.status = TransactionStatus.CANCELLED
            transaction.save()
            
            response_serializer = TransactionDetailSerializer(
                transaction, context={'request': request}
            )
            
            logger.info(f"Transaction cancelled via POST: {transaction.reference_number} by {request.user.email}")
            
            return Response(
                {
                    'message': 'Transaction cancelled successfully',
                    'transaction': response_serializer.data
                }
            )
        except Exception as e:
            logger.error(f"Transaction POST cancellation error: {str(e)}")
            return Response(
                {'error': 'Transaction cancellation failed. Please try again later.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Get transaction statistics",
        description="""
        Retrieve comprehensive statistics about the user's transactions.
        
        Returns:
        - Count of transactions by status (pending, processing, completed, failed, cancelled)
        - Total transaction amounts grouped by currency
        - Overall transaction count
        
        Useful for dashboards and transaction overview displays.
        """,
        responses={
            200: {
                "type": "object",
                "properties": {
                    "total_transactions": {"type": "integer"},
                    "pending_transactions": {"type": "integer"},
                    "processing_transactions": {"type": "integer"},
                    "completed_transactions": {"type": "integer"},
                    "failed_transactions": {"type": "integer"},
                    "cancelled_transactions": {"type": "integer"},
                    "total_amount_by_currency": {
                        "type": "object",
                        "additionalProperties": {"type": "number"}
                    }
                }
            },
            401: {"description": "Authentication required"}
        },
        examples=[
            OpenApiExample(
                'Statistics Response',
                summary='Example statistics response',
                description='Sample response showing user transaction statistics',
                value={
                    "total_transactions": 25,
                    "pending_transactions": 5,
                    "processing_transactions": 3,
                    "completed_transactions": 15,
                    "failed_transactions": 1,
                    "cancelled_transactions": 1,
                    "total_amount_by_currency": {
                        "USD": 15000.00,
                        "EUR": 8500.00,
                        "GBP": 2000.00
                    }
                },
            ),
        ],
        tags=["Transaction Analytics"]
    )
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get user's transaction statistics."""
        user_transactions = self.get_queryset()
        
        stats = {
            'total_transactions': user_transactions.count(),
            'pending_transactions': user_transactions.filter(status=TransactionStatus.PENDING).count(),
            'processing_transactions': user_transactions.filter(status=TransactionStatus.PROCESSING).count(),
            'completed_transactions': user_transactions.filter(status=TransactionStatus.COMPLETED).count(),
            'failed_transactions': user_transactions.filter(status=TransactionStatus.FAILED).count(),
            'cancelled_transactions': user_transactions.filter(status=TransactionStatus.CANCELLED).count(),
        }
        
        # Calculate totals by currency for completed transactions
        completed_transactions = user_transactions.filter(status=TransactionStatus.COMPLETED)
        currency_totals = {}
        
        for transaction in completed_transactions:
            currency = transaction.currency
            if currency not in currency_totals:
                currency_totals[currency] = 0
            currency_totals[currency] += float(transaction.amount)
        
        stats['total_amount_by_currency'] = currency_totals
        
        return Response(stats)
    
    @extend_schema(
        summary="Get transaction documents",
        description="""
        Retrieve all documents associated with a specific transaction.
        
        Returns organized document information including:
        - User payment slip (proof of payment)
        - Receiver barcode image  
        - Admin completion documents (if transaction is completed)
        - File URLs for download/preview
        
        Each document includes type, file object, and accessible URL.
        """,
        responses={
            200: {
                "type": "object",
                "properties": {
                    "transaction_id": {"type": "integer"},
                    "reference_number": {"type": "string"},
                    "documents": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string"},
                                "file": {"type": "object"},
                                "url": {"type": "string"}
                            }
                        }
                    }
                }
            },
            401: {"description": "Authentication required"},
            404: {"description": "Transaction not found"}
        },
        tags=["Transaction Documents"]
    )
    @action(detail=True, methods=['get'])
    def documents(self, request, pk=None):
        """Get all documents associated with a transaction."""
        transaction = self.get_object()
        documents = transaction.supporting_documents
        
        return Response({
            'transaction_id': transaction.id,
            'reference_number': transaction.reference_number,
            'documents': documents
        })


class AdminTransactionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for admin transaction management.
    
    Allows staff members (is_staff=True) to:
    - View all transaction requests from all users
    - Filter and search transactions with pagination
    - View transaction details (automatically sets PENDING to PROCESSING)
    - Update transaction status and add completion documents
    - Access processing transactions only if they are the processing admin or transaction owner
    
    Business Rules:
    1. When admin views details of PENDING transaction → status changes to PROCESSING
    2. Only the processing admin can view PROCESSING transaction details
    3. User who initiated transaction can always view their own transaction
    4. All admins can view CANCELLED, COMPLETED, FAILED, PENDING transactions
    5. Only PROCESSING admin can update PROCESSING transactions
    """
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ['status', 'currency', 'user', 'processing_admin']
    ordering_fields = ['created_at', 'updated_at', 'amount']
    ordering = ['-created_at']
    search_fields = ['reference_number', 'user__email', 'user__first_name', 'user__last_name', 
                     'receiver_account_name', 'description']
    
    def get_queryset(self):
        """Return all transactions for admin users."""
        if not self.request.user.is_staff:
            return Transaction.objects.none()
        return Transaction.objects.select_related('user', 'processing_admin').all()
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return AdminTransactionListSerializer
        elif self.action in ['update', 'partial_update']:
            return AdminTransactionUpdateSerializer
        return AdminTransactionDetailSerializer
    
    def check_transaction_access(self, transaction):
        """
        Check if current admin can access transaction details.
        
        Rules:
        - All admins can view: PENDING, COMPLETED, FAILED, CANCELLED
        - Only processing admin can view: PROCESSING
        - Transaction owner (user) can always view their transaction
        """
        user = self.request.user
        
        # If user is the transaction owner, always allow
        if transaction.user == user:
            return True
            
        # If user is not staff, deny access
        if not user.is_staff:
            return False
            
        # If transaction is PROCESSING, only processing admin can access
        if transaction.status == TransactionStatus.PROCESSING:
            return transaction.processing_admin == user
            
        # All other statuses can be viewed by any admin
        return True
    
    @extend_schema(
        summary="List all transactions (Admin)",
        description="""
        Retrieve all transactions from all users with admin privileges.
        
        **Admin Features:**
        - View transactions from all users with basic info (user details + transaction ID)
        - Filter by status, currency, user, or processing admin
        - Search across reference numbers, user details, receiver names
        - Get specific transaction details by adding `?transaction_id=123`
        
        **Access Rules:**
        - Only staff members (is_staff=True) can access this endpoint
        - When admin views PENDING transaction details → automatically set to PROCESSING
        - Processing admin is recorded for transaction ownership
        
        **Detail View Restrictions:**
        - PROCESSING transactions can only be viewed by the processing admin
        - All admins can view: PENDING, COMPLETED, FAILED, CANCELLED transactions
        """,
        parameters=[
            OpenApiParameter(
                name='transaction_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Get specific transaction details (may change PENDING to PROCESSING)',
                required=False
            ),
            OpenApiParameter(
                name='status',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by transaction status',
                enum=['pending', 'processing', 'completed', 'failed', 'cancelled'],
                required=False
            ),
            OpenApiParameter(
                name='user',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filter by user ID',
                required=False
            ),
            OpenApiParameter(
                name='processing_admin',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filter by processing admin ID',
                required=False
            ),
        ],
        responses={
            200: {
                "description": "List of transactions or single transaction details. Returns list for general queries, single object when transaction_id is provided."
            },
            403: {"description": "Admin privileges required"},
            404: {"description": "Transaction not found or access denied"}
        },
        tags=["Admin Transactions"]
    )
    def list(self, request, *args, **kwargs):
        """List all transactions for admin or get specific transaction details."""
        # Check if transaction_id is provided in query params
        transaction_id = request.query_params.get('transaction_id')
        
        if transaction_id:
            try:
                # Get specific transaction by ID
                transaction = self.get_queryset().get(id=transaction_id)
                
                # Check access permission
                if not self.check_transaction_access(transaction):
                    return Response(
                        {'error': 'You do not have permission to view this transaction.'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                
                # If transaction is PENDING and user is admin, set to PROCESSING
                if (transaction.status == TransactionStatus.PENDING and 
                    request.user.is_staff and transaction.user != request.user):
                    
                    transaction.status = TransactionStatus.PROCESSING
                    transaction.processing_admin = request.user
                    transaction.save()
                    
                    logger.info(f"Transaction {transaction.reference_number} set to PROCESSING by admin {request.user.email}")
                
                serializer = AdminTransactionDetailSerializer(transaction, context={'request': request})
                return Response(serializer.data)
                
            except Transaction.DoesNotExist:
                return Response(
                    {'error': 'Transaction not found.'},
                    status=status.HTTP_404_NOT_FOUND
                )
            except ValueError:
                return Response(
                    {'error': 'Invalid transaction ID format.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Default list behavior with filtering
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        summary="Update transaction (Admin)",
        description="""
        Update transaction status and add completion documents.
        
        **Admin Update Rules:**
        - PENDING → PROCESSING, FAILED, CANCELLED
        - PROCESSING → COMPLETED, FAILED (only by processing admin)
        - COMPLETED, FAILED, CANCELLED → Cannot be changed
        
        **Completion Requirements:**
        - When marking as COMPLETED, must provide transaction_completion_document
        - Can add internal notes for documentation
        
        **Access Control:**
        - Only processing admin can update PROCESSING transactions
        - Any admin can update PENDING transactions
        """,
        request=AdminTransactionUpdateSerializer,
        responses={
            200: {
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                    "transaction": {"type": "object", "description": "Updated transaction details"}
                }
            },
            400: {"description": "Invalid status transition or validation errors"},
            403: {"description": "Not the processing admin or insufficient permissions"},
            404: {"description": "Transaction not found"}
        },
        tags=["Admin Transactions"]
    )
    def update(self, request, *args, **kwargs):
        """Update transaction status and completion details."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Check if admin can update this transaction
        if not self.check_transaction_access(instance):
            return Response(
                {'error': 'You do not have permission to update this transaction.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Additional check for PROCESSING transactions
        if (instance.status == TransactionStatus.PROCESSING and 
            instance.processing_admin != request.user and 
            instance.user != request.user):
            return Response(
                {
                    'error': 'Only the processing admin can update processing transactions.',
                    'processing_admin': instance.processing_admin.email if instance.processing_admin else None
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Set the admin user for notification purposes
            instance._admin_user = request.user
            transaction = serializer.save()
            
            # Return updated transaction details
            response_serializer = AdminTransactionDetailSerializer(
                transaction, context={'request': request}
            )
            
            logger.info(f"Transaction {transaction.reference_number} updated by admin {request.user.email}")
            
            return Response(
                {
                    'message': 'Transaction updated successfully',
                    'transaction': response_serializer.data
                }
            )
        except Exception as e:
            logger.error(f"Admin transaction update error: {str(e)}")
            return Response(
                {'error': 'Transaction update failed. Please try again later.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Get admin transaction statistics",
        description="""
        Retrieve comprehensive statistics for all transactions (admin view).
        
        Returns system-wide statistics including:
        - Total transactions by status across all users
        - Processing admin workload distribution
        - Transaction volume by currency
        - User activity metrics
        """,
        responses={
            200: {
                "type": "object",
                "properties": {
                    "total_transactions": {"type": "integer"},
                    "pending_transactions": {"type": "integer"},
                    "processing_transactions": {"type": "integer"},
                    "completed_transactions": {"type": "integer"},
                    "failed_transactions": {"type": "integer"},
                    "cancelled_transactions": {"type": "integer"},
                    "processing_by_admin": {"type": "object"},
                    "total_amount_by_currency": {"type": "object"},
                    "active_users": {"type": "integer"}
                }
            },
            403: {"description": "Admin privileges required"}
        },
        tags=["Admin Analytics"]
    )
    @action(detail=False, methods=['get'])
    def admin_statistics(self, request):
        """Get comprehensive transaction statistics for admin."""
        all_transactions = self.get_queryset()
        
        stats = {
            'total_transactions': all_transactions.count(),
            'pending_transactions': all_transactions.filter(status=TransactionStatus.PENDING).count(),
            'processing_transactions': all_transactions.filter(status=TransactionStatus.PROCESSING).count(),
            'completed_transactions': all_transactions.filter(status=TransactionStatus.COMPLETED).count(),
            'failed_transactions': all_transactions.filter(status=TransactionStatus.FAILED).count(),
            'cancelled_transactions': all_transactions.filter(status=TransactionStatus.CANCELLED).count(),
        }
        
        # Processing workload by admin
        processing_transactions = all_transactions.filter(status=TransactionStatus.PROCESSING)
        processing_by_admin = {}
        for transaction in processing_transactions:
            if transaction.processing_admin:
                admin_email = transaction.processing_admin.email
                processing_by_admin[admin_email] = processing_by_admin.get(admin_email, 0) + 1
        
        stats['processing_by_admin'] = processing_by_admin
        
        # Calculate totals by currency for completed transactions
        completed_transactions = all_transactions.filter(status=TransactionStatus.COMPLETED)
        currency_totals = {}
        
        for transaction in completed_transactions:
            currency = transaction.currency
            if currency not in currency_totals:
                currency_totals[currency] = 0
            currency_totals[currency] += float(transaction.amount)
        
        stats['total_amount_by_currency'] = currency_totals
        
        # Active users count
        stats['active_users'] = all_transactions.values('user').distinct().count()
        
        return Response(stats)
