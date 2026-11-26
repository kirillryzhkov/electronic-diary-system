from pathlib import PurePosixPath

from django.db import transaction
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiTypes
from rest_framework import serializers
from rest_framework.exceptions import APIException
from rest_framework.response import Response

from academic.models import HomeworkSubmission
from grades.models import Grade
from .journal import JournalView, record_grade_change, utc_timestamp


class SubmissionQuerySerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=[status for status, _ in HomeworkSubmission.STATUS_CHOICES] + ['all'],
        default='submitted',
    )
    assignment_id = serializers.IntegerField(min_value=1, max_value=2**63 - 1, required=False)


class SubmissionReviewSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['checked', 'returned'])
    grade_value = serializers.IntegerField(min_value=1, max_value=5, allow_null=True, required=False)
    teacher_comment = serializers.CharField(default='', allow_blank=True, trim_whitespace=False)
    audit_reason = serializers.CharField(default='', allow_blank=True)

    def validate(self, attrs):
        if attrs['status'] == 'checked' and attrs.get('grade_value') is None:
            raise serializers.ValidationError({'grade_value': 'Укажи оценку от 1 до 5.'})
        return attrs


class JournalCellOccupied(APIException):
    status_code = 409
    default_detail = 'В журнале уже есть другая оценка за дату сдачи этого задания.'
    default_code = 'journal_cell_occupied'


def submission_counts(submissions):
    totals = {
        row['status']: row['total']
        for row in submissions.order_by().values('status').annotate(total=Count('pk'))
    }
    counts = {status: totals.get(status, 0) for status, _ in HomeworkSubmission.STATUS_CHOICES}
    return {**counts, 'all': sum(counts.values())}


def submission_data(submission):
    homework = submission.homework
    assignment = homework.assignment
    return {
        'id': submission.pk,
        'homework_id': homework.pk,
        'homework_title': homework.title,
        'deadline': homework.deadline.isoformat(),
        'assignment_id': assignment.pk,
        'group_name': assignment.group.name,
        'subject_name': assignment.subject.name,
        'student_id': submission.student_id,
        'student_name': submission.student.full_name,
        'answer_text': submission.answer_text or '',
        'file_url': submission.file.url if submission.file else None,
        'file_name': PurePosixPath(submission.file.name).name if submission.file else None,
        'submitted_at': utc_timestamp(submission.submitted_at),
        'status': submission.status,
        'grade_value': submission.grade_value,
        'teacher_comment': submission.teacher_comment or '',
        'checked_at': utc_timestamp(submission.checked_at) if submission.checked_at else None,
        'grade_id': submission.grade_id,
    }


def save_submission_grade(submission, assignment, actor, data):
    """Save the linked grade within the locked journal assignment."""
    day = submission.homework.deadline
    cell = assignment.journal_grades.filter(student_id=submission.student_id, lesson_date=day)
    if cell.exclude(pk=submission.grade_id).exists():
        raise JournalCellOccupied()

    value = data['grade_value']
    comment = data['teacher_comment']
    fields = {
        'assignment': assignment,
        'lesson_date': day,
        'subject_id': assignment.subject_id,
        'student_id': submission.student_id,
        'teacher': actor,
        'value': value,
        'comment': comment,
    }
    if submission.grade_id is None:
        return Grade.objects.create(**fields)

    grade = Grade.objects.select_for_update().get(pk=submission.grade_id)
    if (grade.value, grade.comment or '') != (value, comment):
        record_grade_change(grade, assignment, actor, value, comment, data['audit_reason'])
    for field, field_value in fields.items():
        setattr(grade, field, field_value)
    grade.save(update_fields=[*fields, 'updated_at'])
    return grade


class HomeworkSubmissionsView(JournalView):
    @extend_schema(parameters=[SubmissionQuerySerializer], responses=OpenApiTypes.OBJECT)
    def get(self, request):
        query = SubmissionQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        assignments = self.assignments()
        if 'assignment_id' in query.validated_data:
            assignment = get_object_or_404(assignments, pk=query.validated_data['assignment_id'])
            assignments = assignments.filter(pk=assignment.pk)

        submissions = HomeworkSubmission.objects.filter(homework__assignment__in=assignments)
        counts = submission_counts(submissions)
        status = query.validated_data['status']
        if status != 'all':
            submissions = submissions.filter(status=status)

        submissions = submissions.select_related(
            'student', 'homework__assignment__group', 'homework__assignment__subject'
        ).order_by('-submitted_at', '-pk')
        return Response({
            'counts': counts,
            'submissions': [submission_data(submission) for submission in submissions],
        })


class HomeworkSubmissionReviewView(JournalView):
    @extend_schema(
        request=SubmissionReviewSerializer,
        responses={200: OpenApiTypes.OBJECT, 409: OpenApiTypes.OBJECT},
    )
    @transaction.atomic
    def post(self, request, submission_id):
        if not 1 <= submission_id <= 2**63 - 1:
            raise Http404

        serializer = SubmissionReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        assignments = self.assignments()
        submissions = HomeworkSubmission.objects.filter(homework__assignment__in=assignments)
        assignment_ids = submissions.filter(pk=submission_id).values('homework__assignment_id')
        # Match the cell endpoint's lock order before updating submission or grade rows.
        assignment = get_object_or_404(
            assignments.select_for_update(), pk__in=assignment_ids
        )
        submission = get_object_or_404(
            HomeworkSubmission.objects.select_for_update(),
            pk=submission_id,
            homework__assignment=assignment,
        )

        submission.status = data['status']
        submission.teacher_comment = data['teacher_comment']
        submission.checked_at = timezone.now()
        if 'grade_value' in data:
            submission.grade_value = data['grade_value']
        if submission.status == 'checked':
            submission.grade = save_submission_grade(submission, assignment, request.user, data)
        submission.save(update_fields=[
            'status', 'teacher_comment', 'checked_at', 'grade_value', 'grade',
        ])
        return Response({
            'submission': submission_data(submission),
            'counts': submission_counts(submissions),
        })
