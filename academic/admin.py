# academic/admin.py
from django.contrib import admin

from .models import StudyGroup, Classroom, TeachingAssignment


@admin.register(StudyGroup)
class StudyGroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'curator')
    list_filter = ('curator',)
    search_fields = ('name', 'curator__username')
    ordering = ('name',)


@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ('id', 'number', 'description')
    search_fields = ('number', 'description')
    ordering = ('number',)


@admin.register(TeachingAssignment)
class TeachingAssignmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'teacher', 'subject', 'group', 'classroom')
    list_filter = ('teacher', 'subject', 'group', 'classroom')
    search_fields = (
        'teacher__username',
        'subject__name',
        'group__name',
        'classroom__number',
    )
    ordering = ('group__name', 'subject__name')