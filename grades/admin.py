from django.contrib import admin
from .models import Grade


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'subject', 'value', 'date')
    list_filter = ('subject', 'value', 'date')
    search_fields = ('student__username', 'student__email', 'subject__name', 'comment')
    ordering = ('-date',)

    fieldsets = (
        ('Основная информация', {
            'fields': ('student', 'subject', 'value')
        }),
        ('Пояснение', {
            'fields': ('comment',)
        }),
    )