from rest_framework.permissions import BasePermission


class IsSenderOrReceiverOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        return bool(request.user.is_staff or request.user.id in [obj.from_user.id, obj.to_user.id])


class IsAdminOrSelf(BasePermission):
    def has_object_permission(self, request, view, obj):
        return bool(request.user.is_staff or request.user.id == obj.id)


class IsAdminOrOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return bool(request.user.is_staff or request.user.id == obj.user.id)