from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """Admin interface for Transaction model."""
    
    list_display = [
        'reference_number',
        'user_email',
        'status',
        'amount_display',
        'receiver_account_name',
        'user_payment_method',
        'created_at',
        'has_files'
    ]
    
    list_filter = [
        'status',
        'currency',
        'user_payment_method',
        'created_at',
        'updated_at'
    ]
    
    search_fields = [
        'reference_number',
        'user__email',
        'user__first_name',
        'user__last_name',
        'receiver_account_name',
        'receiver_account_number',
        'receiver_swift_code',
        'user_payment_method',
        'user_bank_name'
    ]
    
    readonly_fields = [
        'id',
        'reference_number',
        'created_at',
        'updated_at',
        'file_preview'
    ]
    
    fieldsets = (
        ('Transaction Information', {
            'fields': (
                'id',
                'reference_number',
                'user',
                'status',
                'created_at',
                'updated_at'
            )
        }),
        ('Financial Details', {
            'fields': (
                'amount',
                'currency'
            )
        }),
        ('User Payment Details', {
            'fields': (
                'user_payment_method',
                'user_bank_name',
                'user_account_name',
                'user_account_number',
                'user_payment_reference'
            )
        }),
        ('Receiver Information', {
            'fields': (
                'receiver_account_name',
                'receiver_account_number',
                'receiver_swift_code'
            )
        }),
        ('Files & Documents', {
            'fields': (
                'user_payment_slip',
                'receiver_barcode_image',
                'transaction_completion_document',
                'additional_completion_document',
                'file_preview'
            )
        }),
        ('Additional Information', {
            'fields': (
                'description',
                'notes'
            ),
            'classes': ('collapse',)
        })
    )
    
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    def user_email(self, obj):
        """Display user email with link to user admin."""
        url = reverse('admin:users_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.email)
    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'user__email'
    
    def amount_display(self, obj):
        """Display formatted amount."""
        return f"{obj.amount} {obj.currency}"
    amount_display.short_description = 'Amount'
    amount_display.admin_order_field = 'amount'
    
    def has_files(self, obj):
        """Show if transaction has attached files."""
        files_count = len(obj.supporting_documents)
        if files_count > 0:
            return format_html(
                '<span style="color: green;">✓ {} files</span>',
                files_count
            )
        return format_html('<span style="color: red;">✗ No files</span>')
    has_files.short_description = 'Files'
    
    def file_preview(self, obj):
        """Display preview of attached files."""
        if not obj.pk:
            return "Save the transaction first to see file previews"
        
        html = []
        for doc in obj.supporting_documents:
            if doc['file']:
                file_name = doc['file'].name.split('/')[-1]
                html.append(
                    f'<p><strong>{doc["type"].replace("_", " ").title()}:</strong><br>'
                    f'<a href="{doc["url"]}" target="_blank">{file_name}</a></p>'
                )
        
        return mark_safe('<br>'.join(html)) if html else "No files attached"
    file_preview.short_description = 'File Preview'
    
    actions = ['mark_as_processing', 'mark_as_completed', 'mark_as_failed']
    
    def mark_as_processing(self, request, queryset):
        """Mark selected transactions as processing."""
        updated = queryset.update(status=Transaction.TransactionStatus.PROCESSING)
        self.message_user(
            request,
            f'{updated} transactions marked as processing.'
        )
    mark_as_processing.short_description = 'Mark as Processing'
    
    def mark_as_completed(self, request, queryset):
        """Mark selected transactions as completed."""
        from django.utils import timezone
        
        updated = 0
        for transaction in queryset:
            transaction.status = Transaction.TransactionStatus.COMPLETED
            transaction.processed_at = timezone.now()
            transaction.save()
            updated += 1
        
        self.message_user(
            request,
            f'{updated} transactions marked as completed.'
        )
    mark_as_completed.short_description = 'Mark as Completed'
    
    def mark_as_failed(self, request, queryset):
        """Mark selected transactions as failed."""
        updated = queryset.update(status=Transaction.TransactionStatus.FAILED)
        self.message_user(
            request,
            f'{updated} transactions marked as failed.'
        )
    mark_as_failed.short_description = 'Mark as Failed'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('user')
