from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    Check that message retrieved by chat is owner by current user.
    """
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user


class IsOwnerUser(permissions.BasePermission):
    """
    Check that user is asked for object is owner of the chat(obj).
    """
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user
