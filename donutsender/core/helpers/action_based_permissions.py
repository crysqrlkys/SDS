from rest_framework.permissions import BasePermission


class ActionBasedPermission(BasePermission):
    """
    Grant or deny access to a view, based on a mapping in view.action_permissions
    """
    def has_permission(self, request, view):
        for klass, actions in getattr(view, 'action_permissions', {}).items():
            if view.action in actions:
                return klass().has_permission(request, view)
        return False

    def has_object_permission(self, request, view, obj):
        for klass, actions in getattr(view, 'action_permissions', {}).items():
            if view.action in actions:
                return klass().has_object_permission(request, view, obj)
        return False
