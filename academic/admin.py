# academic/admin.py
from django.contrib import admin

from .models import StudyGroup, Classroom, TeachingAssignment, Schedule, Attendance


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

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'day',
        'start_time',
        'end_time',
        'lesson_number',
        'get_teacher',
        'get_subject',
        'get_group',
        'get_classroom',
    )
    list_filter = (
        'day',
        'assignment__teacher',
        'assignment__subject',
        'assignment__group',
        'assignment__classroom',
    )
    search_fields = (
        'assignment__teacher__username',
        'assignment__teacher__first_name',
        'assignment__teacher__last_name',
        'assignment__subject__name',
        'assignment__group__name',
        'assignment__classroom__number',
    )
    ordering = ('day', 'start_time')

    def get_teacher(self, obj):
        return obj.assignment.teacher.full_name

    get_teacher.short_description = 'Преподаватель'

    def get_subject(self, obj):
        return obj.assignment.subject.name

    get_subject.short_description = 'Предмет'

    def get_group(self, obj):
        return obj.assignment.group.name

    get_group.short_description = 'Группа'

    def get_classroom(self, obj):
        return obj.assignment.classroom or '—'

    get_classroom.short_description = 'Кабинет'

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'student',
        'get_teacher',
        'get_subject',
        'get_group',
        'date',
        'status',
    )
    list_filter = (
        'status',
        'date',
        'assignment__teacher',
        'assignment__subject',
        'assignment__group',
    )
    search_fields = (
        'student__username',
        'student__first_name',
        'student__last_name',
        'assignment__teacher__username',
        'assignment__subject__name',
        'assignment__group__name',
    )
    ordering = ('-date',)

    def get_teacher(self, obj):
        return obj.assignment.teacher.full_name

    get_teacher.short_description = 'Преподаватель'

    def get_subject(self, obj):
        return obj.assignment.subject.name

    get_subject.short_description = 'Предмет'

    def get_group(self, obj):
        return obj.assignment.group.name

    get_group.short_description = 'Группа'