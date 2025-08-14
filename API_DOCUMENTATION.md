# Transaction API Documentation

## Overview
This API allows authenticated users to create and manage payment transactions. Users can initiate transactions by providing transaction details, receiver information, user payment details, and upload supporting documents.

## Authentication
All endpoints require authentication. Include the JWT token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

## Base URL
```
/api/transactions/
```

## Endpoints

### 1. Create Transaction
**POST** `/api/transactions/`

Create a new transaction with status set to "pending".

**Request Body** (multipart/form-data or JSON):
```json
{
    "amount": "1000.00",
    "currency": "USD",
    "description": "Payment for services",
    
    // User payment details (how the user is paying)
    "user_payment_method": "Bank Transfer",
    "user_bank_name": "Chase Bank",
    "user_account_name": "John Doe",
    "user_account_number": "1234567890",
    "user_payment_reference": "TXN123456",
    "user_payment_slip": "<file_upload>",
    
    // Receiver details (who is receiving the payment)
    "receiver_account_name": "Jane Smith",
    "receiver_account_number": "9876543210",
    "receiver_swift_code": "CHASUS33",
    "receiver_barcode_image": "<file_upload>"
}
```

**Response** (201 Created):
```json
{
    "message": "Transaction created successfully",
    "transaction": {
        "id": 1,
        "reference_number": "TXN-A1B2C3D4",
        "status": "pending",
        "amount": "1000.00",
        "currency": "USD",
        "created_at": "2025-08-14T10:30:00Z",
        ...
    }
}
```

### 2. List User Transactions
**GET** `/api/transactions/`

Get all transactions for the authenticated user with filtering and pagination.

**Query Parameters:**
- `status`: Filter by status (pending, processing, completed, failed, cancelled)
- `currency`: Filter by currency code
- `search`: Search in reference_number, receiver_account_name, description
- `ordering`: Order by created_at, updated_at, amount (use `-` prefix for descending)

**Response** (200 OK):
```json
{
    "count": 25,
    "next": "http://localhost:8000/api/transactions/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "reference_number": "TXN-A1B2C3D4",
            "user_email": "user@example.com",
            "status": "pending",
            "status_display": "Pending",
            "amount": "1000.00",
            "currency": "USD",
            "currency_display": "US Dollar",
            "receiver_account_name": "Jane Smith",
            "user_payment_method": "Bank Transfer",
            "created_at": "2025-08-14T10:30:00Z",
            ...
        }
    ]
}
```

### 3. Get Transaction Details
**GET** `/api/transactions/{id}/`

Get detailed information about a specific transaction.

**Response** (200 OK):
```json
{
    "id": 1,
    "reference_number": "TXN-A1B2C3D4",
    "user_email": "user@example.com",
    "status": "pending",
    "amount": "1000.00",
    "currency": "USD",
    "description": "Payment for services",
    
    // User payment details
    "user_payment_method": "Bank Transfer",
    "user_bank_name": "Chase Bank",
    "user_account_name": "John Doe",
    "user_account_number": "1234567890",
    "user_payment_reference": "TXN123456",
    
    // Receiver details
    "receiver_account_name": "Jane Smith",
    "receiver_account_number": "9876543210",
    "receiver_swift_code": "CHASUS33",
    
    // Supporting documents
    "supporting_documents": [
        {
            "type": "user_payment_slip",
            "file": "<file_object>",
            "url": "https://storage.googleapis.com/..."
        },
        {
            "type": "barcode_image",
            "file": "<file_object>",
            "url": "https://storage.googleapis.com/..."
        }
    ],
    
    "created_at": "2025-08-14T10:30:00Z",
    "updated_at": "2025-08-14T10:30:00Z"
}
```

### 4. Update Transaction
**PUT/PATCH** `/api/transactions/{id}/`

Update transaction details. Only allowed for transactions in "pending" status.

**Request Body** (similar to create, but all fields optional for PATCH):
```json
{
    "description": "Updated description",
    "user_payment_reference": "NEW_REF123",
    "receiver_account_name": "Updated Receiver Name"
}
```

### 5. Cancel Transaction
**DELETE** `/api/transactions/{id}/`

Cancel a pending transaction (sets status to "cancelled").

**Response** (200 OK):
```json
{
    "message": "Transaction cancelled successfully"
}
```

### 6. Custom Actions

#### Get Pending Transactions
**GET** `/api/transactions/pending/`

Get all pending transactions for the user.

#### Get Completed Transactions
**GET** `/api/transactions/completed/`

Get all completed transactions for the user.

#### Get Transaction Statistics
**GET** `/api/transactions/statistics/`

Get user's transaction statistics.

**Response**:
```json
{
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
}
```

#### Cancel Transaction (Alternative)
**POST** `/api/transactions/{id}/cancel/`

Alternative method to cancel a transaction.

#### Get Transaction Documents
**GET** `/api/transactions/{id}/documents/`

Get all documents associated with a transaction.

## File Upload Guidelines

### Supported File Types
- **Payment Slips**: PDF, JPG, JPEG, PNG
- **Barcode Images**: PDF, JPG, JPEG, PNG, GIF
- **Completion Documents**: PDF, JPG, JPEG, PNG, DOC, DOCX

### File Size Limits
- Maximum file size: 10MB per file
- Multiple files can be uploaded per transaction

### File Storage
- Files are stored in Google Cloud Platform (GCP) Cloud Storage
- During development, files may be stored locally
- All files are validated for type and size before upload

## Error Handling

### Common Error Responses

**400 Bad Request**:
```json
{
    "error": "Cannot update transaction that is not in pending status."
}
```

**401 Unauthorized**:
```json
{
    "detail": "Authentication credentials were not provided."
}
```

**403 Forbidden**:
```json
{
    "detail": "You do not have permission to perform this action."
}
```

**404 Not Found**:
```json
{
    "detail": "Not found."
}
```

**Validation Errors (400)**:
```json
{
    "amount": ["Transaction amount must be greater than zero."],
    "receiver_swift_code": ["SWIFT code must be 8 or 11 characters long."],
    "user_payment_details": ["If providing payment details, all fields are required. Missing: user_bank_name"]
}
```

## Workflow Example

1. **User creates transaction**:
   ```bash
   POST /api/transactions/
   # Upload payment slip, receiver barcode, fill all details
   # Status: "pending"
   ```

2. **User can update if needed**:
   ```bash
   PATCH /api/transactions/1/
   # Only works while status is "pending"
   ```

3. **Admin processes transaction** (admin interface):
   - Reviews user payment details and documents
   - Changes status to "processing"
   - Uploads completion documents when done
   - Changes status to "completed"

4. **User can view completed transaction**:
   ```bash
   GET /api/transactions/1/
   # See all documents including admin completion docs
   ```

## Currency Support

The API supports 80+ world currencies including:
- Major: USD, EUR, GBP, JPY, CHF, CAD, AUD, NZD
- Asian: CNY, INR, KRW, SGD, HKD, THB, MYR, IDR, PHP, VND, TWD
- Middle East & Africa: AED, SAR, QAR, KWD, BHD, OMR, ILS, EGP, ZAR, NGN, KES, GHS
- European (non-Euro): NOK, SEK, DKK, PLN, CZK, HUF, RON, BGN, HRK, RUB, UAH, TRY
- Latin American: BRL, MXN, ARS, CLP, COP, PEN, UYU, BOB, PYG
- Cryptocurrencies: BTC, ETH
- Precious metals: XAU (Gold), XAG (Silver)
