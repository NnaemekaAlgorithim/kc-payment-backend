# Firebase Cloud Messaging (FCM) Setup Guide

## Required Environment Variables

You need to obtain these three keys from Firebase Console:

```bash
FCM_SERVER_KEY=your-server-key-here
FCM_SENDER_ID=your-sender-id-here
FCM_WEB_API_KEY=your-web-api-key-here
```

## Step-by-Step Setup

### 1. Create Firebase Project
1. Visit [Firebase Console](https://console.firebase.google.com/)
2. Click "Add project" or "Create a project"
3. Enter project name: `kc-payment-backend` (or your preferred name)
4. Continue through setup (Google Analytics optional)

### 2. Get FCM Server Key (Legacy)
1. In Firebase Console, go to **Project Settings** (⚙️ gear icon)
2. Navigate to **Cloud Messaging** tab
3. Scroll down to **Project credentials** section
4. Copy the **Server key** value
   - This is your `FCM_SERVER_KEY`
   - Format: `AAAAxxxxxxx:APA91bH...` (very long string)

### 3. Get Sender ID
1. Still in **Project Settings** → **Cloud Messaging**
2. Find **Sender ID** under **Project credentials**
   - This is your `FCM_SENDER_ID`
   - Format: 12-digit number like `123456789012`

### 4. Get Web API Key
1. In **Project Settings**, go to **General** tab
2. Scroll down to **Your apps** section
3. If no web app exists, click **Add app** → **Web** (</>) icon
4. Register your web app with a nickname
5. Copy the **Web API Key** from the config object
   - This is your `FCM_WEB_API_KEY`
   - Format: `AIzaSyB...` (starts with AIzaSy)

### 5. Update Environment Variables

Add these to your `.env` file:

```bash
# Firebase Cloud Messaging (FCM) Configuration
FCM_SERVER_KEY=AAAAxxxxxxx:APA91bH_your_actual_server_key_here
FCM_SENDER_ID=123456789012
FCM_WEB_API_KEY=AIzaSyB_your_actual_web_api_key_here
```

## Testing in Development

### 1. Create Migrations and Run Server

```bash
# Create and apply migrations
python manage.py makemigrations notifications
python manage.py migrate

# Create a superuser (if not already done)
python manage.py createsuperuser

# Run the development server
python manage.py runserver
```

### 2. Test with Django Admin

1. Visit `http://127.0.0.1:8000/admin/`
2. Log in with your superuser credentials
3. Navigate to **Notifications** section
4. You should see:
   - **Notifications**
   - **FCM devices**
   - **Notification preferences**

### 3. Test API Endpoints

The notification system provides these REST API endpoints:

```bash
# Get user notifications
GET /api/notifications/

# Mark notifications as read
POST /api/notifications/mark_read/
{
    "notification_ids": [1, 2, 3]
}

# Get notification statistics
GET /api/notifications/statistics/

# Register FCM device
POST /api/fcm-devices/
{
    "device_token": "device_token_from_client",
    "device_type": "web",
    "device_name": "Chrome Browser"
}

# Get notification preferences
GET /api/notification-preferences/1/

# Update notification preferences
PATCH /api/notification-preferences/1/
{
    "email_transaction_created": true,
    "push_transaction_created": false
}
```

### 4. Test Push Notifications

#### Option A: Using Django Shell

```python
# Open Django shell
python manage.py shell

# Test notification creation
from django.contrib.auth import get_user_model
from payment.apps.notifications.services import notification_service

User = get_user_model()
user = User.objects.first()  # Get a test user

# Create a test notification
notification_service.create_notification(
    recipient=user,
    title="Test Notification",
    message="This is a test push notification",
    notification_type="TRANSACTION_CREATED"
)
```

#### Option B: Create Test Transaction

```python
# In Django shell
from payment.apps.transactions.models import Transaction
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.first()

# Create a transaction (this will trigger notification signals)
transaction = Transaction.objects.create(
    user=user,
    amount=100.00,
    currency='USD',
    # ... other required fields
)
```

### 5. Test with Real Device Tokens

To test actual push notifications, you'll need:

1. **Web App**: Implement Firebase SDK in your frontend
2. **Mobile App**: Use Firebase SDK for Android/iOS
3. **Device Registration**: Register device tokens via the API

#### Sample Web Implementation (JavaScript):

```javascript
// Initialize Firebase in your web app
import { initializeApp } from 'firebase/app';
import { getMessaging, getToken } from 'firebase/messaging';

const firebaseConfig = {
    apiKey: "your-web-api-key",
    authDomain: "your-project.firebaseapp.com",
    projectId: "your-project-id",
    storageBucket: "your-project.appspot.com",
    messagingSenderId: "your-sender-id",
    appId: "your-app-id"
};

const app = initializeApp(firebaseConfig);
const messaging = getMessaging(app);

// Get FCM token
getToken(messaging, { 
    vapidKey: 'your-vapid-key' // Generate this in Firebase Console
}).then((currentToken) => {
    if (currentToken) {
        // Send token to your backend
        fetch('/api/fcm-devices/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer your-jwt-token'
            },
            body: JSON.stringify({
                device_token: currentToken,
                device_type: 'web',
                device_name: 'Chrome Browser'
            })
        });
    }
});
```

## Troubleshooting

### Common Issues:

1. **Invalid Server Key**: Ensure you're using the Server key from Cloud Messaging tab
2. **CORS Errors**: Add your domain to Firebase authorized domains
3. **Token Registration Failed**: Check if device token is valid and user is authenticated
4. **No Notifications Received**: Verify device is registered and active in Django admin

### Debug Steps:

1. Check Django logs for notification creation
2. Verify FCM device registration in admin
3. Test notification creation manually in Django shell
4. Check Firebase Console for delivery reports

## Production Considerations

1. **Security**: Store FCM keys securely (use environment variables)
2. **Rate Limiting**: Implement rate limiting for device registration
3. **Token Refresh**: Handle token refresh in client applications
4. **Error Handling**: Implement proper error handling for failed notifications
5. **Monitoring**: Set up logging and monitoring for notification delivery
