from datetime import timedelta
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from academic.models import Attendance, Classroom, Homework, HomeworkSubmission
from academic.models import Schedule, StudyGroup, TeachingAssignment
from grades.models import Grade, GradeAuditLog
from subjects.models import Subject
from users.models import User


class SeedDemoTests(TestCase):
    def test_seed_populates_current_week_and_preserves_records_on_repeat(self):
        unrelated = User.objects.create_user(username='existing')
        call_command('seed_demo', stdout=StringIO())
        students = User.objects.filter(username__startswith='student')
        self.assertEqual(students.count(), 8)
        self.assertEqual(students.values('group_id').distinct().count(), 2)
        for username in ('admin', 'teacher', 'teacher2', 'student1', 'student2', 'student3', 'student4'):
            self.assertTrue(User.objects.get(username=username).check_password('password123'))

        today = timezone.localdate()
        monday = today - timedelta(days=today.weekday())
        saturday = monday + timedelta(days=5)
        self.assertEqual(Grade.objects.filter(
            assignment__isnull=False, lesson_date__range=(monday, saturday),
        ).count(), 32)
        self.assertEqual(Attendance.objects.filter(date__range=(monday, saturday)).count(), 32)
        self.assertEqual(GradeAuditLog.objects.count(), 3)
        for entry in GradeAuditLog.objects.all():
            self.assertTrue(entry.reason)
            self.assertNotEqual(entry.old_value, entry.new_value)
            self.assertEqual(Grade.objects.get(pk=entry.grade_id).value, entry.new_value)

        client = APIClient()
        teacher = User.objects.get(username='teacher')
        client.force_authenticate(teacher)
        queue = client.get(reverse('homework-submissions'), {'status': 'all'}).data
        self.assertEqual(queue['counts'], {'submitted': 1, 'checked': 1, 'returned': 1, 'all': 3})
        assignment = TeachingAssignment.objects.get(teacher=teacher, subject__name='Математика')
        journal = client.get(reverse('journal-grid'), {'assignment_id': assignment.pk}).data
        self.assertEqual(len(journal['students']), 4)
        self.assertTrue(all(
            row['cells'][monday.isoformat()]['grade'] and row['cells'][monday.isoformat()]['attendance']
            for row in journal['students']
        ))

        client.force_authenticate(User.objects.get(username='admin'))
        analytics = client.get(reverse('analytics-overview')).data
        self.assertEqual(analytics['summary']['risk_count'], 2)
        self.assertEqual(
            {row['student_id'] for row in analytics['risk_students']},
            set(students.filter(username__in=['student7', 'student8']).values_list('pk', flat=True)),
        )
        self.assertEqual(HomeworkSubmission.objects.count(), 6)
        for submission in HomeworkSubmission.objects.filter(status='checked').select_related('grade'):
            self.assertEqual(submission.grade.lesson_date, submission.homework.deadline)
            self.assertEqual(submission.grade.value, submission.grade_value)

        grade = Grade.objects.filter(assignment=assignment).first()
        grade.comment = 'Ручная правка'
        grade.save()
        models = (
            User, StudyGroup, Subject, Classroom, TeachingAssignment, Schedule,
            Grade, Attendance, GradeAuditLog, Homework, HomeworkSubmission,
        )
        before = [list(model.objects.order_by('pk').values()) for model in models]
        call_command('seed_demo', stdout=StringIO())
        self.assertEqual(before, [list(model.objects.order_by('pk').values()) for model in models])
        self.assertTrue(User.objects.filter(pk=unrelated.pk).exists())
