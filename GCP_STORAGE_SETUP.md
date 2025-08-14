# Google Cloud Platform (GCP) Storage Setup Guide

This guide will help you set up Google Cloud Platform Cloud Storage for handling file uploads in your payment backend application.

## Prerequisites

1. Google Cloud Platform account
2. A GCP project
3. Billing enabled on your GCP project

## Step 1: Create GCP Project & Enable APIs

### 1.1 Create a New Project (or use existing)
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Enter project name: `kc-payment-backend` (or your preferred name)
4. Note the **Project ID** (you'll need this)

### 1.2 Enable Required APIs
1. In Google Cloud Console, go to **APIs & Services** → **Library**
2. Search and enable these APIs:
   - **Cloud Storage API**
   - **Cloud Storage JSON API**

## Step 2: Create Storage Bucket

### 2.1 Create Bucket
1. Go to **Cloud Storage** → **Buckets**
2. Click **Create bucket**
3. Bucket name: `kc-payment-files` (globally unique name required)
4. Choose location: **us-central1** (or your preferred region)
5. Storage class: **Standard**
6. Access control: **Fine-grained** (recommended for security)
7. Click **Create**

### 2.2 Configure Bucket Permissions
1. Go to your bucket → **Permissions** tab
2. Click **Grant Access**
3. Add your service account (we'll create this next) with role: **Storage Object Admin**

## Step 3: Create Service Account

### 3.1 Create Service Account
1. Go to **IAM & Admin** → **Service Accounts**
2. Click **Create Service Account**
3. Name: `kc-payment-storage`
4. Description: `Service account for KC Payment file uploads`
5. Click **Create and Continue**

### 3.2 Assign Roles
Add these roles to your service account:
- **Storage Admin** (for full bucket management)
- **Storage Object Admin** (for file management)

### 3.3 Create and Download Key
1. Click on your newly created service account
2. Go to **Keys** tab
3. Click **Add Key** → **Create new key**
4. Choose **JSON** format
5. Download and save the JSON file securely
6. **IMPORTANT**: Keep this file secure and never commit it to version control

## Step 4: Configure Django Settings

### 4.1 Install Required Package
```bash
pip install google-cloud-storage
```

### 4.2 Update Environment Variables

Add these to your `.env` file:

```bash
# Google Cloud Platform (GCP) Storage Settings
USE_GCP_STORAGE=True
GCP_PROJECT_ID=your-actual-project-id
GCP_STORAGE_BUCKET_NAME=kc-payment-files
GCP_SERVICE_ACCOUNT_FILE=/path/to/your/service-account-key.json
GCP_LOCATION=us-central1
GCP_FILE_OVERWRITE=False
GCP_DEFAULT_ACL=publicRead
```

**Alternative: Using JSON String Instead of File**
If you prefer to use the JSON content directly (useful for deployment):

```bash
GCP_SERVICE_ACCOUNT_JSON={"type":"service_account","project_id":"your-project",...}
```

### 4.3 Verify Django Configuration
Your `base_settings.py` should already be configured. Verify these sections exist:

```python
# File Storage Configuration
if USE_GCP_STORAGE:
    DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
    STATICFILES_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
    
    GS_BUCKET_NAME = GCP_STORAGE_BUCKET_NAME
    GS_PROJECT_ID = GCP_PROJECT_ID
    # ... other settings
```

## Step 5: Testing File Uploads

### 5.1 Test with Django Shell
```python
# Open Django shell
python manage.py shell

# Test file upload
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

# Create a test file
test_content = b"This is a test file for GCP storage"
test_file = ContentFile(test_content, name="test.txt")

# Save to storage
file_path = default_storage.save("test/test.txt", test_file)
print(f"File saved at: {file_path}")

# Get file URL
file_url = default_storage.url(file_path)
print(f"File URL: {file_url}")

# Verify file exists
exists = default_storage.exists(file_path)
print(f"File exists: {exists}")
```

### 5.2 Test Transaction Creation with Files

#### Using cURL:
```bash
# Create a test transaction with file uploads
curl -X POST http://localhost:8000/api/transactions/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: multipart/form-data" \
  -F "amount=500.00" \
  -F "currency=USD" \
  -F "receiver_account_name=Test Receiver" \
  -F "receiver_account_number=1234567890" \
  -F "receiver_swift_code=TESTUS33XXX" \
  -F "description=Test transaction with files" \
  -F "user_payment_method=Bank Transfer" \
  -F "user_bank_name=Test Bank" \
  -F "user_payment_slip=@/path/to/test-receipt.pdf" \
  -F "receiver_barcode_image=@/path/to/test-barcode.jpg"
```

#### Using Postman:
1. Set method to **POST**
2. URL: `http://localhost:8000/api/transactions/`
3. Headers:
   - `Authorization: Bearer YOUR_JWT_TOKEN`
4. Body: Select **form-data**
5. Add fields:
   - `amount`: 500.00
   - `currency`: USD
   - `receiver_account_name`: Test Receiver
   - `receiver_account_number`: 1234567890
   - `receiver_swift_code`: TESTUS33XXX
   - `user_payment_slip`: (File upload)
   - `receiver_barcode_image`: (File upload)

#### Using Python requests:
```python
import requests

url = 'http://localhost:8000/api/transactions/'
headers = {
    'Authorization': 'Bearer YOUR_JWT_TOKEN'
}

data = {
    'amount': '500.00',
    'currency': 'USD',
    'receiver_account_name': 'Test Receiver',
    'receiver_account_number': '1234567890',
    'receiver_swift_code': 'TESTUS33XXX',
    'description': 'Test transaction',
    'user_payment_method': 'Bank Transfer',
    'user_bank_name': 'Test Bank'
}

files = {
    'user_payment_slip': ('receipt.pdf', open('test-receipt.pdf', 'rb'), 'application/pdf'),
    'receiver_barcode_image': ('barcode.jpg', open('test-barcode.jpg', 'rb'), 'image/jpeg')
}

response = requests.post(url, headers=headers, data=data, files=files)
print(response.json())
```

## Step 6: File Upload Validation

The system validates uploaded files:

### Supported File Types:
- **Payment Slip**: PDF, JPG, JPEG, PNG, GIF (max 10MB)
- **Barcode Image**: JPG, JPEG, PNG, GIF (max 5MB)

### File Path Structure:
Files are stored in GCP with this path structure:
```
transactions/{user_id}/{transaction_id}/{unique_filename}
```

Example:
```
transactions/123/456/a1b2c3d4e5f6.pdf
transactions/123/456/f6e5d4c3b2a1.jpg
```

## Step 7: Security Best Practices

### 7.1 Service Account Security
- Store service account JSON file outside your project root
- Never commit service account keys to version control
- Use environment variables for all sensitive data
- Consider using Google Cloud IAM for production deployments

### 7.2 Bucket Security
- Use fine-grained access control
- Enable uniform bucket-level access if needed
- Set up proper CORS policies for web uploads
- Monitor access logs

### 7.3 File Access Control
- Files are stored with `publicRead` ACL by default
- Consider using signed URLs for sensitive files
- Implement proper user authentication before file access

## Development vs Production

### Development (Local)
- Set `USE_GCP_STORAGE=False` for local file storage
- Files stored in `media/` directory
- Easier for testing and development

### Production
- Set `USE_GCP_STORAGE=True`
- All files stored in GCP Cloud Storage
- Better scalability and reliability
- CDN capabilities

## Troubleshooting

### Common Issues:

1. **Authentication Error**
   - Verify service account JSON file path
   - Check if file has correct permissions
   - Ensure service account has required roles

2. **Bucket Permission Error**
   - Verify bucket name in settings
   - Check if service account has Storage Admin role
   - Ensure bucket exists and is accessible

3. **File Upload Failed**
   - Check file size limits
   - Verify file type is supported
   - Ensure proper Content-Type headers

4. **URLs Not Working**
   - Verify `GCP_DEFAULT_ACL=publicRead` setting
   - Check bucket CORS configuration
   - Ensure files have public read permissions

### Debug Commands:
```python
# Test storage connection
from django.core.files.storage import default_storage
print(default_storage.location)
print(default_storage.bucket_name)

# List files in storage
files = default_storage.listdir('')
print(files)

# Test file operations
exists = default_storage.exists('test-file.txt')
print(f"File exists: {exists}")
```

## Cost Optimization

- Use lifecycle policies to delete old files
- Consider storage classes (Standard, Nearline, Coldline)
- Monitor usage and costs in GCP Console
- Implement file cleanup for cancelled/failed transactions

For more information, refer to:
- [Google Cloud Storage Documentation](https://cloud.google.com/storage/docs)
- [Django Storages Documentation](https://django-storages.readthedocs.io/en/latest/backends/gcloud.html)
