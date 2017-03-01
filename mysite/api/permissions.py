from rest_framework import permissions


class IsInstructor(permissions.BasePermission):
    """
    Check that user is asked for object is owner/user of the course(obj).
    """
    def has_object_permission(self, request, view, obj):
        return obj.addedBy == request.user
