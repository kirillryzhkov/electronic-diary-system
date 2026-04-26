from django.contrib import admin
from .models import User
from django.contrib.auth.models import Group

admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'last_name', 'first_name', 'email', 'role', 'group', 'is_active', 'is_staff')
    list_filter = ('role', 'group', 'is_active', 'is_staff')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('id',)

    fieldsets = (
        ('Личная информация', {
            'fields': ('username', 'email', 'password')
        }),
        ('Роль и группа', {
            'fields': ('role', 'group')
        }),
        ('Права доступа', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Даты', {
            'fields': ('last_login',)
        }),
    )