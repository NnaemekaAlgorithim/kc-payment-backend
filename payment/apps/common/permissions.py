from rest_framework import permissions
from rest_framework.permissions import BasePermission


class IsOwnerOrReadOnly(BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    message = "You must be the owner of this object to modify it."

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the object.
        return obj.created_by == request.user if hasattr(obj, 'created_by') else True


class IsAdminOrReadOnly(BasePermission):
    """
    Custom permission to only allow admins to modify objects.
    """
    message = "You must be an admin to modify this object."

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


class IsSuperUserOnly(BasePermission):
    """
    Permission to allow only superusers to access the endpoint.
    """
    message = "You must be a superuser to access this endpoint."

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_superuser


class IsStaffOrReadOnly(BasePermission):
    """
    Permission to allow only staff members to modify objects.
    """
    message = "You must be a staff member to modify this object."

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


class IsAuthenticatedOrCreateOnly(BasePermission):
    """
    Permission to allow unauthenticated users to create objects,
    but require authentication for other operations.
    """
    message = "Authentication required for this operation."

    def has_permission(self, request, view):
        if request.method == 'POST':
            return True
        return request.user and request.user.is_authenticated


class IsOwnerOrAdmin(BasePermission):
    """
    Permission to allow owners or admins to access/modify objects.
    """
    message = "You must be the owner or an admin to access this object."

    def has_object_permission(self, request, view, obj):
        # Admin can access/modify any object
        if request.user and request.user.is_staff:
            return True
        
        # Owner can access/modify their own object
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'owner'):
            return obj.owner == request.user
        
        return False


class ReadOnlyPermission(BasePermission):
    """
    Permission that only allows read-only access.
    """
    message = "Read-only access."

    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS


class IsActiveUser(BasePermission):
    """
    Permission to check if user is active.
    """
    message = "Your account is not active."

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_active


class HasGroupPermission(BasePermission):
    """
    Permission to check if user belongs to a specific group.
    Usage: Add required_groups attribute to the view.
    """
    message = "You don't have the required group permissions."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        required_groups = getattr(view, 'required_groups', None)
        if not required_groups:
            return True
        
        user_groups = request.user.groups.values_list('name', flat=True)
        return any(group in user_groups for group in required_groups)


class DynamicPermission(BasePermission):
    """
    Dynamic permission class that can be configured per view.
    Usage: Add permission_classes_by_action to the view.
    """
    
    def has_permission(self, request, view):
        action = getattr(view, 'action', None)
        permission_classes_by_action = getattr(view, 'permission_classes_by_action', {})
        
        if action in permission_classes_by_action:
            for permission_class in permission_classes_by_action[action]:
                permission = permission_class()
                if not permission.has_permission(request, view):
                    self.message = getattr(permission, 'message', 'Permission denied.')
                    return False
        
        return True


# Utility functions for permission checking
def user_has_permission(user, permission_name):
    """
    Check if user has a specific permission.
    """
    return user.has_perm(permission_name) if user and user.is_authenticated else False


def user_in_group(user, group_name):
    """
    Check if user is in a specific group.
    """
    if not user or not user.is_authenticated:
        return False
    return user.groups.filter(name=group_name).exists()


def is_object_owner(user, obj):
    """
    Check if user is the owner of an object.
    """
    if not user or not user.is_authenticated:
        return False
    
    # Check various owner fields
    owner_fields = ['created_by', 'user', 'owner', 'author']
    for field in owner_fields:
        if hasattr(obj, field):
            return getattr(obj, field) == user
    
    return False
