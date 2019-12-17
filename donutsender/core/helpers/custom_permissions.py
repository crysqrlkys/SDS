from rest_framework.permissions import BasePermission


class IsSenderOrReceiverOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        return bool(request.user.is_staff or request.user.id in [obj.from_user.id, obj.to_user.id])

    def has_permission(self, request, view):
        return bool(request.user.is_authenticated)


class IsAdminOrSelf(BasePermission):
    def has_object_permission(self, request, view, obj):
        return bool(request.user.is_staff or request.user.id == obj.id)

    def has_permission(self, request, view):
        return bool(request.user.is_authenticated)


class IsAdminOrOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return bool(request.user.is_staff or request.user.id == obj.user.id)
