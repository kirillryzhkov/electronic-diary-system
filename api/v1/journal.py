from collections import defaultdict
from datetime import timedelta, timezone as datetime_timezone

from django.db import transaction
from django.http import Http404
from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiTypes
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from academic.models import Attendance, TeachingAssignment
from grades.models import Grade, GradeAuditLog
from notifications_app.services import notify_user
from .journal_serializers import JournalCellSerializer, JournalQuerySerializer


WEEKDAYS = ('Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб')
ATTENDED_STATUSES = ('present', 'late')


def assignment_data(assignment):
    return {
        'id': assignment.pk,
        'group_id': assignment.group_id,
        'group_name': assignment.group.name,
        'subject_id': assignment.subject_id,
        'subject_name': assignment.subject.name,
        'teacher_id': assignment.teacher_id,
        'teacher_name': assignment.teacher.full_name,
    }


def utc_timestamp(value):
    return value.astimezone(datetime_timezone.utc).isoformat().replace('+00:00', 'Z')


def cell_data(attendance, grade):
    return {
        'attendance': {
            'id': attendance.pk,
            'status': attendance.status,
            'comment': attendance.comment or '',
        } if attendance else None,
        'grade': {
            'id': grade.pk,
            'value': grade.value,
            'comment': grade.comment or '',
            'teacher_name': grade.teacher.full_name if grade.teacher else '',
            'updated_at': utc_timestamp(grade.updated_at or grade.date),
            'audit_count': grade.audit_count,
        } if grade else None,
    }


def student_stats(assignment, student_ids):
    """Calculate totals across the assignment, independent of the displayed week."""
    grades = journal_grades(assignment).filter(student_id__in=student_ids)
    attendance = assignment.attendance_records.filter(student_id__in=student_ids)
    averages = {
        row['student_id']: round(row['average'], 2)
        for row in grades.order_by().values('student_id').annotate(average=Avg('value'))
    }
    rates = {
        row['student_id']: round(100 * row['attended'] / row['total'], 2)
        for row in attendance.order_by().values('student_id').annotate(
            total=Count('pk'),
            attended=Count('pk', filter=Q(status__in=ATTENDED_STATUSES)),
        )
    }
    return {
        student_id: {
            'avg_grade': averages.get(student_id, 0.0),
            'attendance_rate': rates.get(student_id, 0.0),
        }
        for student_id in student_ids
    }


def journal_grades(assignment):
    return assignment.journal_grades.filter(lesson_date__isnull=False)


def grades_with_cell_details(grades, assignment):
    grades = list(grades.select_related('teacher'))
    counts = {
        row['grade_id']: row['total']
        for row in GradeAuditLog.objects.filter(
            assignment=assignment, grade_id__in=[grade.pk for grade in grades]
        ).order_by().values('grade_id').annotate(total=Count('pk'))
    }
    for grade in grades:
        grade.audit_count = counts.get(grade.pk, 0)
    return grades


def save_attendance(assignment, student, data):
    if 'attendance_status' not in data:
        return
    records = assignment.attendance_records
    lookup = {'student': student, 'date': data['date']}
    if not data['attendance_status']:
        records.filter(**lookup).delete()
        return

    defaults = {'status': data['attendance_status']}
    if 'attendance_comment' in data:
        defaults['comment'] = data['attendance_comment']
    was_absent = (
        defaults['status'] == 'absent' and records.filter(**lookup, status='absent').exists()
    )
    records.update_or_create(**lookup, defaults=defaults)
    if defaults['status'] == 'absent' and not was_absent:
        notify_user(
            student, 'attendance', 'Отмечен пропуск',
            f'{assignment.subject.name}, {data["date"]:%d.%m.%Y}.',
        )


def save_grade(grades, assignment, student, actor, data):
    delete_grade = data.get('delete_grade', False) or (
        'grade_value' in data and data['grade_value'] is None
    )
    if not delete_grade and 'grade_value' not in data and 'grade_comment' not in data:
        return

    grade = grades.first()
    if grade is None:
        if not delete_grade and 'grade_value' in data:
            assignment.journal_grades.create(
                student=student,
                lesson_date=data['date'],
                teacher=assignment.teacher,
                subject=assignment.subject,
                value=data['grade_value'],
                comment=data.get('grade_comment', ''),
            )
            notify_user(
                student, 'grade', 'Новая оценка',
                f'{assignment.subject.name}: {data["grade_value"]}.',
            )
        return

    old_comment = grade.comment or ''
    new_value = None if delete_grade else data.get('grade_value', grade.value)
    new_comment = '' if delete_grade else data.get('grade_comment', old_comment)
    if (grade.value, old_comment) == (new_value, new_comment):
        return

    record_grade_change(grade, assignment, actor, new_value, new_comment, data.get('audit_reason', ''))
    if delete_grade:
        grade.delete()
    else:
        grade.value = new_value
        grade.comment = new_comment
        grade.save(update_fields=['value', 'comment', 'updated_at'])
        notify_user(
            student, 'grade', 'Оценка изменена', f'{assignment.subject.name}: {new_value}.',
        )


def record_grade_change(grade, assignment, actor, new_value, new_comment, reason):
    """Record a grade edit or deletion before changing the original row."""
    old_comment = grade.comment or ''
    GradeAuditLog.objects.create(
        grade_id=grade.pk,
        assignment=assignment,
        changed_by=actor,
        changed_by_name=actor.full_name,
        old_value=grade.value,
        new_value=new_value,
        old_comment=old_comment,
        new_comment=new_comment,
        reason=reason,
    )


class CanAccessJournal(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ('admin', 'teacher')


class JournalView(APIView):
    permission_classes = [CanAccessJournal]

    def assignments(self):
        assignments = TeachingAssignment.objects.all()
        if self.request.user.role == 'teacher':
            assignments = assignments.filter(teacher=self.request.user)
        return assignments


class JournalAssignmentsView(JournalView):
    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        assignments = self.assignments().select_related('group', 'subject', 'teacher')
        return Response({'assignments': [assignment_data(item) for item in assignments]})


class JournalGridView(JournalView):
    @extend_schema(parameters=[JournalQuerySerializer], responses=OpenApiTypes.OBJECT)
    def get(self, request):
        return Response(self.week_data(request.query_params))

    def week_data(self, query_params):
        """Build the shared weekly data for the JSON grid and spreadsheet."""
        query = JournalQuerySerializer(data=query_params)
        query.is_valid(raise_exception=True)
        assignment = get_object_or_404(
            self.assignments().select_related('group', 'subject', 'teacher'),
            pk=query.validated_data['assignment_id'],
        )
        today = timezone.localdate()
        start = query.validated_data.get('week_start', today - timedelta(days=today.weekday()))
        end = start + timedelta(days=5)
        students = list(assignment.group.students.filter(role='student').order_by(
            'last_name', 'first_name', 'pk'
        ))
        student_ids = [student.pk for student in students]
        stats = student_stats(assignment, student_ids)
        marks = assignment.attendance_records.filter(
            student_id__in=student_ids, date__range=(start, end)
        )
        grades = journal_grades(assignment).filter(
            student_id__in=student_ids, lesson_date__range=(start, end)
        )
        marks_by_cell = {(mark.student_id, mark.date): mark for mark in marks}
        grades_by_cell = {
            (grade.student_id, grade.lesson_date): grade
            for grade in grades_with_cell_details(grades, assignment)
        }

        times = defaultdict(list)
        for lesson in assignment.schedule_items.all():
            times[lesson.day].append(f'{lesson.start_time:%H:%M}–{lesson.end_time:%H:%M}')

        week_days = [start + timedelta(days=index) for index in range(len(WEEKDAYS))]
        dates = []
        for index, (weekday, day) in enumerate(zip(WEEKDAYS, week_days)):
            day_times = times[index + 1]
            dates.append({
                'date': day.isoformat(),
                'weekday': index + 1,
                'label': f'{weekday} {day:%d.%m}',
                'has_lesson': bool(day_times),
                'lesson_time': ', '.join(day_times),
            })

        assignment_details = assignment_data(assignment)
        assignment_details.pop('teacher_id')
        return {
            'assignment': assignment_details,
            'week_start': start.isoformat(),
            'week_end': end.isoformat(),
            'prev_week': (start - timedelta(days=7)).isoformat(),
            'next_week': (start + timedelta(days=7)).isoformat(),
            'dates': dates,
            'students': [
                {
                    'id': student.pk,
                    'username': student.username,
                    'full_name': student.full_name,
                    **stats[student.pk],
                    'cells': {
                        day.isoformat(): cell_data(
                            marks_by_cell.get((student.pk, day)),
                            grades_by_cell.get((student.pk, day)),
                        )
                        for day in week_days
                    },
                }
                for student in students
            ],
        }


class JournalCellView(JournalView):
    @extend_schema(request=JournalCellSerializer, responses={200: OpenApiTypes.OBJECT})
    @transaction.atomic
    def post(self, request):
        serializer = JournalCellSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        # Serialize journal writes for this assignment, including empty cells.
        assignment = get_object_or_404(
            self.assignments().select_for_update(), pk=data['assignment_id']
        )
        student = get_object_or_404(
            assignment.group.students, pk=data['student_id'], role='student'
        )
        day = data['date']
        marks = assignment.attendance_records.filter(student=student, date=day)
        grades = journal_grades(assignment).filter(student=student, lesson_date=day)
        save_attendance(assignment, student, data)
        save_grade(grades, assignment, student, request.user, data)
        grade = next(iter(grades_with_cell_details(grades, assignment)), None)
        return Response({
            'student_id': student.pk,
            'date': day.isoformat(),
            'cell': cell_data(marks.first(), grade),
            **student_stats(assignment, [student.pk])[student.pk],
        })


class JournalGradeHistoryView(JournalView):
    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request, grade_id):
        if not 1 <= grade_id <= 2**63 - 1:
            raise Http404
        assignments = self.assignments()
        history = list(GradeAuditLog.objects.filter(assignment__in=assignments, grade_id=grade_id))
        if not history:
            get_object_or_404(
                Grade.objects.filter(assignment__in=assignments, lesson_date__isnull=False),
                pk=grade_id,
            )
        return Response({
            'grade_id': grade_id,
            'history': [
                {
                    'id': entry.pk,
                    'changed_by_name': entry.changed_by_name,
                    'old_value': entry.old_value,
                    'new_value': entry.new_value,
                    'old_comment': entry.old_comment,
                    'new_comment': entry.new_comment,
                    'reason': entry.reason,
                    'changed_at': utc_timestamp(entry.changed_at),
                }
                for entry in history
            ],
        })
