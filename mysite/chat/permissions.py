from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    Check that user is asked for object is owner/user of the chat(obj).
    """
    def has_object_permission(self, request, view, obj):
        check_result = False
        try:
            check_result = (obj.user == request.user)
        except AttributeError:
            check_result = (obj.owner == request.user)
        finally:
            return check_result
