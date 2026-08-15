from rest_framework.permissions import BasePermission

class IsModerator(BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name="Модераторы").exists()

    def has_object_permission(self, request, view, obj):
        return request.user.groups.filter(name="Модераторы").exists()


class IsOwner(BasePermission):
    """Проверка, является ли пользователь владельцем объекта"""

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user

class IsSelfUser(BasePermission):
    """Проверка, что пользователь обращается к собственному профилю."""
    def has_object_permission(self, request, view, obj):
        return obj == request.user