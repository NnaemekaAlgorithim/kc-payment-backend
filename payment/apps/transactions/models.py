from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator
from payment.apps.common.models import BaseModel
from payment.apps.users.models import User
from .storage import validate_barcode_image, validate_supporting_document


def transaction_file_upload_path(instance, filename):
    """Generate upload path for transaction files."""
    import uuid
    from pathlib import Path
    
    # Generate a unique filename while preserving the extension
    file_extension = Path(filename).suffix
    unique_filename = f"{uuid.uuid4().hex}{file_extension}"
    
    return f'transactions/{instance.user.id}/{instance.id}/{unique_filename}'


class TransactionStatus(models.TextChoices):
    """Transaction status choices."""
    PENDING = 'pending', 'Pending'
    PROCESSING = 'processing', 'Processing'
    COMPLETED = 'completed', 'Completed'
    FAILED = 'failed', 'Failed'
    CANCELLED = 'cancelled', 'Cancelled'


class CurrencyChoices(models.TextChoices):
    """World currency choices (ISO 4217)."""
    # Major currencies
    USD = 'USD', 'US Dollar'
    EUR = 'EUR', 'Euro'
    GBP = 'GBP', 'British Pound'
    JPY = 'JPY', 'Japanese Yen'
    CHF = 'CHF', 'Swiss Franc'
    CAD = 'CAD', 'Canadian Dollar'
    AUD = 'AUD', 'Australian Dollar'
    NZD = 'NZD', 'New Zealand Dollar'
    
    # Asian currencies
    CNY = 'CNY', 'Chinese Yuan'
    INR = 'INR', 'Indian Rupee'
    KRW = 'KRW', 'South Korean Won'
    SGD = 'SGD', 'Singapore Dollar'
    HKD = 'HKD', 'Hong Kong Dollar'
    THB = 'THB', 'Thai Baht'
    MYR = 'MYR', 'Malaysian Ringgit'
    IDR = 'IDR', 'Indonesian Rupiah'
    PHP = 'PHP', 'Philippine Peso'
    VND = 'VND', 'Vietnamese Dong'
    TWD = 'TWD', 'Taiwan Dollar'
    
    # Middle East & Africa
    AED = 'AED', 'UAE Dirham'
    SAR = 'SAR', 'Saudi Riyal'
    QAR = 'QAR', 'Qatari Riyal'
    KWD = 'KWD', 'Kuwaiti Dinar'
    BHD = 'BHD', 'Bahraini Dinar'
    OMR = 'OMR', 'Omani Rial'
    ILS = 'ILS', 'Israeli Shekel'
    EGP = 'EGP', 'Egyptian Pound'
    ZAR = 'ZAR', 'South African Rand'
    NGN = 'NGN', 'Nigerian Naira'
    KES = 'KES', 'Kenyan Shilling'
    GHS = 'GHS', 'Ghanaian Cedi'
    
    # European currencies (non-Euro)
    NOK = 'NOK', 'Norwegian Krone'
    SEK = 'SEK', 'Swedish Krona'
    DKK = 'DKK', 'Danish Krone'
    PLN = 'PLN', 'Polish Zloty'
    CZK = 'CZK', 'Czech Koruna'
    HUF = 'HUF', 'Hungarian Forint'
    RON = 'RON', 'Romanian Leu'
    BGN = 'BGN', 'Bulgarian Lev'
    HRK = 'HRK', 'Croatian Kuna'
    RUB = 'RUB', 'Russian Ruble'
    UAH = 'UAH', 'Ukrainian Hryvnia'
    TRY = 'TRY', 'Turkish Lira'
    
    # Latin American currencies
    BRL = 'BRL', 'Brazilian Real'
    MXN = 'MXN', 'Mexican Peso'
    ARS = 'ARS', 'Argentine Peso'
    CLP = 'CLP', 'Chilean Peso'
    COP = 'COP', 'Colombian Peso'
    PEN = 'PEN', 'Peruvian Sol'
    UYU = 'UYU', 'Uruguayan Peso'
    BOB = 'BOB', 'Bolivian Boliviano'
    PYG = 'PYG', 'Paraguayan Guarani'
    
    # Other notable currencies
    RMB = 'RMB', 'Chinese Renminbi'
    XAU = 'XAU', 'Gold Ounce'
    XAG = 'XAG', 'Silver Ounce'
    BTC = 'BTC', 'Bitcoin'
    ETH = 'ETH', 'Ethereum'


class Transaction(BaseModel):
    """
    Transaction model for handling payment transactions.
    Inherits from BaseModel to get id, created_at, and updated_at fields.
    """
    # User relationship
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='transactions',
        help_text="User who initiated the transaction"
    )
    
    # Transaction details
    status = models.CharField(
        max_length=20,
        choices=TransactionStatus.choices,
        default=TransactionStatus.PENDING,
        help_text="Current status of the transaction"
    )
    
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Transaction amount"
    )
    
    currency = models.CharField(
        max_length=3,
        choices=CurrencyChoices.choices,
        default=CurrencyChoices.USD,
        help_text="Currency code (ISO 4217)"
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Transaction description or memo"
    )
    
    # User payment details (how the user is paying)
    user_payment_method = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Payment method used by user (e.g., Bank Transfer, Credit Card, etc.)"
    )
    
    user_bank_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="User's bank name for the payment"
    )
    
    user_account_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="User's account holder name"
    )
    
    user_account_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^[0-9\-\s]*$',
                message='Account number can only contain numbers, hyphens, and spaces'
            )
        ],
        help_text="User's account number used for payment"
    )
    
    user_payment_reference = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Payment reference number from user's bank/payment method"
    )
    
    # User payment slip/proof
    user_payment_slip = models.FileField(
        upload_to=transaction_file_upload_path,
        blank=True,
        null=True,
        validators=[validate_supporting_document],
        help_text="User's payment slip or proof of payment (PDF, image, etc.)"
    )
    
    # Receiver details
    receiver_account_name = models.CharField(
        max_length=255,
        help_text="Name of the receiver's account holder"
    )
    
    receiver_account_number = models.CharField(
        max_length=50,
        validators=[
            RegexValidator(
                regex=r'^[0-9\-\s]+$',
                message='Account number can only contain numbers, hyphens, and spaces'
            )
        ],
        help_text="Receiver's account number"
    )
    
    receiver_swift_code = models.CharField(
        max_length=11,
        validators=[
            RegexValidator(
                regex=r'^[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?$',
                message='Invalid SWIFT code format'
            )
        ],
        help_text="Receiver's bank SWIFT/BIC code"
    )
    
    # File storage - GCP Cloud Storage or local storage for development
    receiver_barcode_image = models.FileField(
        upload_to=transaction_file_upload_path,
        blank=True,
        null=True,
        validators=[validate_barcode_image],
        help_text="Receiver's barcode picture (PDF, PNG, JPG, etc.) - stored in GCP Cloud Storage"
    )
    
    # Transaction completion documents (uploaded by admin when completing transaction)
    transaction_completion_document = models.FileField(
        upload_to=transaction_file_upload_path,
        blank=True,
        null=True,
        validators=[validate_supporting_document],
        help_text="Transaction completion document uploaded by admin (receipt, confirmation, etc.)"
    )
    
    additional_completion_document = models.FileField(
        upload_to=transaction_file_upload_path,
        blank=True,
        null=True,
        validators=[validate_supporting_document],
        help_text="Additional completion document if needed (PDF, image, etc.)"
    )
    
    # Additional transaction metadata
    reference_number = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        null=True,
        help_text="Unique transaction reference number"
    )
    
    # Processing admin tracking
    processing_admin = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processing_transactions',
        help_text="Admin user who is currently processing this transaction"
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Internal notes for the transaction"
    )
    
    class Meta:
        db_table = 'payment_transactions'
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['reference_number']),
            models.Index(fields=['created_at']),
            models.Index(fields=['processing_admin']),
        ]
    
    def __str__(self):
        return f"Transaction {self.reference_number or self.id} - {self.user.email} - {self.amount} {self.currency}"
    
    def save(self, *args, **kwargs):
        # Generate reference number if not provided
        if not self.reference_number:
            import uuid
            self.reference_number = f"TXN-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
    
    @property
    def barcode_file_url(self):
        """Get the URL for the barcode file."""
        if self.receiver_barcode_image:
            return self.receiver_barcode_image.url
        return None
    
    @property
    def processing_admin_email(self):
        """Get processing admin email."""
        return self.processing_admin.email if self.processing_admin else None
    
    @property
    def processing_admin_id(self):
        """Get processing admin ID."""
        return self.processing_admin.id if self.processing_admin else None
    
    @property
    def supporting_documents(self):
        """Get list of all transaction documents."""
        documents = []
        if self.user_payment_slip:
            documents.append({
                'type': 'user_payment_slip',
                'file': self.user_payment_slip,
                'url': self.user_payment_slip.url
            })
        if self.receiver_barcode_image:
            documents.append({
                'type': 'barcode_image',
                'file': self.receiver_barcode_image,
                'url': self.receiver_barcode_image.url
            })
        if self.transaction_completion_document:
            documents.append({
                'type': 'completion_document',
                'file': self.transaction_completion_document,
                'url': self.transaction_completion_document.url
            })
        if self.additional_completion_document:
            documents.append({
                'type': 'additional_completion_document',
                'file': self.additional_completion_document,
                'url': self.additional_completion_document.url
            })
        return documents
