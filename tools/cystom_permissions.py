from rest_framework.permissions import BasePermission


class IsOwnerOrAdmin(BasePermission):
    """Access have only author and staff"""
    def has_object_permission(self, request, view, obj):
        return bool(request.user.is_staff or request.user.id == obj.created_by.id)
