# api/v1/permissions.py
from rest_framework import permissions


class IsTeacher(permissions.BasePermission):
    message = 'Доступ разрешён только учителю.'

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'role', None) == 'teacher'
        )


class IsStudent(permissions.BasePermission):
    message = 'Доступ разрешён только ученику.'

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'role', None) == 'student'
        )


class IsGradeOwnerOrTeacher(permissions.BasePermission):
    message = 'Вы можете просматривать только свои оценки. Изменять оценки может только учитель.'

    def has_object_permission(self, request, view, obj):
        role = getattr(request.user, 'role', None)

        # Учитель может просматривать, редактировать и удалять любые оценки.
        if role == 'teacher':
            return True

        # Ученик может только просматривать свои оценки.
        if role == 'student':
            return (
                request.method in permissions.SAFE_METHODS
                and obj.student_id == request.user.id
            )

        return False
