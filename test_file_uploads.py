#!/usr/bin/env python
"""
Test script for transaction file uploads.

This script helps you test file uploads to the transaction endpoint.
It can work with both local storage (development) and GCP storage (production).
"""

import os
import sys
import django
import requests
import json
from pathlib import Path

# Add the project to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'payment.payment.settings.dev_settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class TransactionFileTester:
    """Test file uploads for transactions."""
    
    def __init__(self):
        self.base_url = 'http://127.0.0.1:8000'
        # Check if there's a BASE_PREFIX
        from django.conf import settings
        base_prefix = getattr(settings, 'BASE_PREFIX', '')
        if base_prefix:
            self.api_url = f'{self.base_url}/{base_prefix}/api'
        else:
            self.api_url = f'{self.base_url}/api'
        print(f"Using API URL: {self.api_url}")
        self.token = None
        
    def create_test_files(self):
        """Create test files for upload."""
        test_files_dir = project_root / 'test_files'
        test_files_dir.mkdir(exist_ok=True)
        
        # Create test payment slip (PDF-like content)
        payment_slip_path = test_files_dir / 'test_payment_slip.pdf'
        with open(payment_slip_path, 'w') as f:
            f.write("Test Payment Slip Document\n")
            f.write("Transaction Reference: TEST-001\n")
            f.write("Amount: $500.00\n")
            f.write("Date: 2025-08-14\n")
            f.write("Bank: Test Bank\n")
            f.write("Account: 1234567890\n")
            f.write("This is a mock PDF file for testing purposes.\n")
        
        # Create test barcode image using PIL
        barcode_path = test_files_dir / 'test_barcode.png'
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Create a simple test image
            img = Image.new('RGB', (200, 100), color='white')
            draw = ImageDraw.Draw(img)
            
            # Draw a simple rectangle as a "barcode"
            draw.rectangle([20, 30, 180, 70], outline='black', width=2)
            draw.text((30, 40), "TEST BARCODE", fill='black')
            draw.text((30, 55), "1234567890", fill='black')
            
            img.save(barcode_path, 'PNG')
            
        except ImportError:
            # Fallback: create a minimal PNG file manually
            # This is a minimal 1x1 PNG image in bytes
            png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x00\x01\x00\x18\xdd\x8d\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
            with open(barcode_path, 'wb') as f:
                f.write(png_data)
        
        return payment_slip_path, barcode_path
    
    def get_auth_token(self, email='admin@test.com'):
        """Get JWT token for testing."""
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            print(f"Creating test user: {email}")
            user = User.objects.create_user(
                email=email,
                password='testpassword123',
                first_name='Test',
                last_name='User',
                is_staff=True
            )
        
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    
    def test_transaction_creation(self, with_files=True):
        """Test creating a transaction with or without files."""
        self.token = self.get_auth_token()
        
        # Prepare transaction data
        data = {
            'amount': '500.00',
            'currency': 'USD',
            'description': 'Test transaction with file uploads',
            'user_payment_method': 'Bank Transfer',
            'user_bank_name': 'Test Bank',
            'user_account_name': 'Test User',
            'user_account_number': '1234567890',
            'user_payment_reference': 'TEST-REF-001',
            'receiver_account_name': 'Test Receiver Company',
            'receiver_account_number': '9876543210',
            'receiver_swift_code': 'TESTUS33XXX',
        }
        
        headers = {
            'Authorization': f'Bearer {self.token}'
        }
        
        files = None
        if with_files:
            payment_slip_path, barcode_path = self.create_test_files()
            files = {
                'user_payment_slip': (
                    'payment_slip.pdf',
                    open(payment_slip_path, 'rb'),
                    'application/pdf'
                ),
                'receiver_barcode_image': (
                    'barcode.png',
                    open(barcode_path, 'rb'),
                    'image/png'
                )
            }
        
        try:
            response = requests.post(
                f'{self.api_url}/transactions/',
                headers=headers,
                data=data,
                files=files
            )
            
            if files:
                # Close file handles
                for file_obj in files.values():
                    file_obj[1].close()
            
            print(f"Status Code: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            
            if response.status_code == 201:
                transaction_data = response.json().get('transaction', {})
                print("\n✅ Transaction created successfully!")
                print(f"Transaction ID: {transaction_data.get('id')}")
                print(f"Reference: {transaction_data.get('reference_number')}")
                
                # Check file URLs
                supporting_docs = transaction_data.get('supporting_documents', [])
                if supporting_docs:
                    print("\n📁 Uploaded Files:")
                    for doc in supporting_docs:
                        print(f"- {doc['type']}: {doc['url']}")
                else:
                    print("\n📁 No files uploaded or file URLs not available")
            else:
                print("\n❌ Transaction creation failed!")
                
        except Exception as e:
            print(f"Error: {e}")
            if files:
                # Ensure files are closed on error
                for file_obj in files.values():
                    try:
                        file_obj[1].close()
                    except:
                        pass
    
    def test_storage_configuration(self):
        """Test storage configuration."""
        from django.conf import settings
        from django.core.files.storage import default_storage
        from django.core.files.base import ContentFile
        
        print("🔧 Storage Configuration Test")
        print("=" * 50)
        
        # Check settings
        use_gcp = getattr(settings, 'USE_GCP_STORAGE', False)
        print(f"USE_GCP_STORAGE: {use_gcp}")
        
        if use_gcp:
            print(f"GCP Project ID: {getattr(settings, 'GS_PROJECT_ID', 'Not set')}")
            print(f"GCP Bucket Name: {getattr(settings, 'GS_BUCKET_NAME', 'Not set')}")
            print(f"Storage Backend: {settings.DEFAULT_FILE_STORAGE}")
        else:
            print("Using local file storage for development")
            print(f"Media Root: {settings.MEDIA_ROOT}")
            print(f"Media URL: {settings.MEDIA_URL}")
        
        # Test file operations
        print("\n📝 Testing file operations...")
        try:
            # Create a test file
            test_content = ContentFile(b"Test file content for storage test")
            test_path = default_storage.save('test/storage_test.txt', test_content)
            
            print(f"✅ File saved at: {test_path}")
            
            # Get file URL
            file_url = default_storage.url(test_path)
            print(f"✅ File URL: {file_url}")
            
            # Check if file exists
            exists = default_storage.exists(test_path)
            print(f"✅ File exists: {exists}")
            
            # Clean up test file
            default_storage.delete(test_path)
            print("✅ Test file cleaned up")
            
        except Exception as e:
            print(f"❌ Storage test failed: {e}")
    
    def run_all_tests(self):
        """Run all tests."""
        print("🚀 Transaction File Upload Tests")
        print("=" * 50)
        
        # Test storage configuration
        self.test_storage_configuration()
        
        print("\n" + "=" * 50)
        print("Testing transaction creation without files...")
        self.test_transaction_creation(with_files=False)
        
        print("\n" + "=" * 50)
        print("Testing transaction creation with files...")
        self.test_transaction_creation(with_files=True)


if __name__ == '__main__':
    tester = TransactionFileTester()
    tester.run_all_tests()
