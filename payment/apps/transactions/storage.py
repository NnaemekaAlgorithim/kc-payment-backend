"""
Custom storage utilities for transaction file uploads.
"""
import os
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import UploadedFile


class TransactionFileValidator:
    """Validator for transaction file uploads."""
    
    ALLOWED_EXTENSIONS = {
        'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'],
        'pdf': ['.pdf'],
        'document': ['.pdf', '.doc', '.docx', '.txt']
    }
    
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    @classmethod
    def validate_file(cls, file: UploadedFile, file_type='image'):
        """
        Validate uploaded file.
        
        Args:
            file: The uploaded file
            file_type: Type of file ('image', 'pdf', 'document')
        
        Raises:
            ValidationError: If file is invalid
        """
        if not file:
            return
        
        # Check file size
        if file.size > cls.MAX_FILE_SIZE:
            raise ValidationError(
                f'File size too large. Maximum allowed size is {cls.MAX_FILE_SIZE / (1024*1024):.1f}MB'
            )
        
        # Check file extension
        file_extension = os.path.splitext(file.name)[1].lower()
        allowed_extensions = cls.ALLOWED_EXTENSIONS.get(file_type, [])
        
        if file_extension not in allowed_extensions:
            raise ValidationError(
                f'Invalid file type. Allowed types: {", ".join(allowed_extensions)}'
            )
        
        # Additional validation for images
        if file_type == 'image':
            cls._validate_image(file)
    
    @classmethod
    def _validate_image(cls, file: UploadedFile):
        """Additional validation for image files."""
        try:
            from PIL import Image
            
            # Reset file pointer
            file.seek(0)
            
            # Try to open and verify the image
            with Image.open(file) as img:
                img.verify()
            
            # Reset file pointer after verification
            file.seek(0)
            
        except Exception as e:
            raise ValidationError(f'Invalid image file: {str(e)}')


def validate_barcode_image(file):
    """Validator for barcode image files."""
    TransactionFileValidator.validate_file(file, 'image')


def validate_pdf_document(file):
    """Validator for PDF documents."""
    TransactionFileValidator.validate_file(file, 'pdf')


def validate_supporting_document(file):
    """Validator for supporting documents."""
    TransactionFileValidator.validate_file(file, 'document')


class GCPStorageHelper:
    """Helper class for GCP storage operations."""
    
    @staticmethod
    def get_file_url(file_field):
        """
        Get the public URL for a file stored in GCP.
        
        Args:
            file_field: Django FileField instance
            
        Returns:
            str: Public URL of the file or None if file doesn't exist
        """
        if not file_field:
            return None
        
        try:
            return file_field.url
        except:
            return None
    
    @staticmethod
    def delete_file(file_field):
        """
        Delete a file from storage.
        
        Args:
            file_field: Django FileField instance
            
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        if not file_field:
            return False
        
        try:
            default_storage.delete(file_field.name)
            return True
        except:
            return False
