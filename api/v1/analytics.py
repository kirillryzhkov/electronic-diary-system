from django.db.models import Avg, Count, Exists, OuterRef, Q
from drf_spectacular.utils import extend_schema, OpenApiTypes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from academic.models import Attendance, Homework, HomeworkSubmission, TeachingAssignment
from grades.models import Grade
from users.models import User
from .journal import ATTENDED_STATUSES


def subject_stats(grades):
    rows = grades.order_by('subject__name').values('subject__name').annotate(
        average=Avg('value'), count=Count('pk')
    )
    return [
        {
            'subject_name': row['subject__name'],
            'avg_grade': round(row['average'], 2),
            'grades_count': row['count'],
        }
        for row in rows
    ]


def attendance_counts():
    return {
        'total': Count('pk'),
        'attended': Count('pk', filter=Q(status__in=ATTENDED_STATUSES)),
    }


def attendance_rate(row):
    return round(100 * row['attended'] / row['total'], 2) if row['total'] else 0.0


def student_overview(student):
    grades = student.grades.all()
    unfinished_homework = Homework.objects.filter(assignment__group_id=student.group_id).filter(
        ~Exists(HomeworkSubmission.objects.filter(
            homework_id=OuterRef('pk'), student=student, status__in=('submitted', 'checked')
        ))
    )
    return {
        'role': student.role,
        'summary': {
            'avg_grade': round(grades.aggregate(average=Avg('value'))['average'] or 0.0, 2),
            'attendance_rate': attendance_rate(
                student.attendance_records.aggregate(**attendance_counts())
            ),
            'unread_notifications': student.notifications.filter(is_read=False).count(),
            'pending_homework': unfinished_homework.count(),
        },
        'subjects': subject_stats(grades),
    }


def staff_overview(user):
    assignments = TeachingAssignment.objects.all()
    if user.role == 'teacher':
        assignments = assignments.filter(teacher=user)

    students = User.objects.filter(
        role='student', group_id__in=assignments.order_by().values('group_id')
    )
    # Older grades can be attributed by group and subject. For a teacher, require authorship too.
    matching_legacy_assignment = assignments.filter(
        group_id=OuterRef('student__group_id'), subject_id=OuterRef('subject_id')
    )
    legacy = Q(assignment__isnull=True) & Q(Exists(matching_legacy_assignment))
    if user.role == 'teacher':
        legacy &= Q(teacher=user)
    grades = Grade.objects.filter(student__in=students).filter(
        Q(assignment__in=assignments) | legacy
    )
    attendance = Attendance.objects.filter(assignment__in=assignments, student__in=students)
    pending = HomeworkSubmission.objects.filter(
        homework__assignment__in=assignments, status='submitted'
    ).count()

    averages = {
        row['student_id']: round(row['average'], 2)
        for row in grades.order_by().values('student_id').annotate(average=Avg('value'))
    }
    rates = {
        row['student_id']: attendance_rate(row)
        for row in attendance.order_by().values('student_id').annotate(**attendance_counts())
    }
    risk_students = []
    for student in students.select_related('group').order_by('group__name', 'last_name', 'first_name', 'pk'):
        avg = averages.get(student.pk)
        rate = rates.get(student.pk)
        reasons = []
        if avg is not None and avg < 3.5:
            reasons.append('Низкий ср. балл')
        if rate is not None and rate < 75:
            reasons.append('Низкая посещаемость')
        if reasons:
            risk_students.append({
                'student_id': student.pk,
                'student_name': student.full_name,
                'group_name': student.group.name,
                'avg_grade': avg if avg is not None else 0.0,
                'attendance_rate': rate if rate is not None else 0.0,
                'reasons': reasons,
            })

    return {
        'role': user.role,
        'summary': {
            'students_count': len(students),
            'risk_count': len(risk_students),
            'pending_homework': pending,
            'avg_grade': round(grades.aggregate(average=Avg('value'))['average'] or 0.0, 2),
        },
        'risk_students': risk_students,
        'subjects': subject_stats(grades),
    }


class AnalyticsOverviewView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        user = request.user
        return Response(
            staff_overview(user) if user.role in ('teacher', 'admin') else student_overview(user)
        )
