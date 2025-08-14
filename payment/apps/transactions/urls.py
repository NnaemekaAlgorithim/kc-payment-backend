from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'transactions', views.TransactionViewSet, basename='transaction')
router.register(r'admin/transactions', views.AdminTransactionViewSet, basename='admin-transaction')

app_name = 'transactions'

urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),
]

# Generated URL patterns from the router:
# 
# User Transaction Operations:
# GET    /api/transactions/                    - List user's transactions
# GET    /api/transactions/?transaction_id=123 - Get specific transaction details  
# GET    /api/transactions/?status=pending     - Filter transactions by status
# GET    /api/transactions/?status=completed   - Filter completed transactions
# GET    /api/transactions/?status=cancelled   - Filter cancelled transactions
# POST   /api/transactions/                    - Create new transaction
# PUT    /api/transactions/{id}/               - Update transaction (pending only)
# PATCH  /api/transactions/{id}/               - Update transaction (partial, pending only)
# DELETE /api/transactions/{id}/               - Cancel transaction
#
# Custom user actions:
# POST   /api/transactions/{id}/cancel/        - Cancel transaction (alternative)
# GET    /api/transactions/statistics/         - Get user transaction statistics
# GET    /api/transactions/{id}/documents/     - Get transaction documents
#
# Admin Transaction Operations:
# GET    /api/admin/transactions/                    - List all transactions (admin)
# GET    /api/admin/transactions/?transaction_id=123 - Get specific transaction (may set PENDING→PROCESSING)
# PUT    /api/admin/transactions/{id}/               - Update transaction status (admin)
# PATCH  /api/admin/transactions/{id}/               - Partially update transaction (admin)
# GET    /api/admin/transactions/admin_statistics/   - Get system-wide transaction statistics
