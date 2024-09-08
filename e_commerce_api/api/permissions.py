from rest_framework import permissions

class IsUser(permissions.BasePermission):
    def has_permission(self, request, view):
        # Check if the user is authenticated and their role is either 'user'
        return request.user.role == 'user'

class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        # Check if the user is authenticated and their role is 'admin'
        return request.user.role == 'admin'
