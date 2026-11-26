from datetime import date
from io import BytesIO

from django.test import TestCase
from django.urls import reverse
from openpyxl import load_workbook
from rest_framework.test import APIClient

from academic.models import Attendance, Homework, HomeworkSubmission, StudyGroup, TeachingAssignment
from grades.models import Grade, GradeAuditLog
from subjects.models import Subject
from users.models import User


class HomeworkReviewAndExportTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        group = StudyGroup.objects.create(name='ИС-31')
        subject = Subject.objects.create(name='Информатика')
        cls.teacher = User.objects.create_user(username='teacher', role='teacher')
        cls.other_teacher = User.objects.create_user(username='other', role='teacher')
        cls.admin = User.objects.create_user(username='admin', role='admin')
        cls.student = User.objects.create_user(username='student', last_name='=2+2', group=group)
        cls.assignment = TeachingAssignment.objects.create(
            teacher=cls.teacher, subject=subject, group=group
        )
        cls.other_assignment = TeachingAssignment.objects.create(
            teacher=cls.other_teacher, subject=subject, group=group
        )
        cls.deadline = date(2026, 11, 26)
        homework = Homework.objects.create(
            assignment=cls.assignment, title='Лабораторная №1', deadline=cls.deadline
        )
        cls.submission = HomeworkSubmission.objects.create(
            homework=homework, student=cls.student, answer_text='Ответ',
            file='homework_submissions/2026/11/26/lab1.pdf',
        )
        other_homework = Homework.objects.create(
            assignment=cls.other_assignment, title='Лабораторная №2', deadline=cls.deadline
        )
        cls.other_submission = HomeworkSubmission.objects.create(
            homework=other_homework, student=cls.student, status='returned'
        )

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.teacher)
        self.week = {'assignment_id': self.assignment.pk, 'week_start': '2026-11-23'}

    def review(self, submission=None, **fields):
        submission = self.submission if submission is None else submission
        return self.client.post(
            reverse('homework-submission-review', args=[submission.pk]), fields, format='json'
        )

    def queue(self, **query):
        return self.client.get(reverse('homework-submissions'), query)

    def test_queue_filters_submissions_and_counts_within_accessible_assignments(self):
        response = self.queue()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['counts'], {
            'submitted': 1, 'checked': 0, 'returned': 0, 'all': 1,
        })
        item, = response.data['submissions']
        self.assertEqual(item, {
            'id': self.submission.pk,
            'homework_id': self.submission.homework_id,
            'homework_title': 'Лабораторная №1',
            'deadline': '2026-11-26',
            'assignment_id': self.assignment.pk,
            'group_name': 'ИС-31',
            'subject_name': 'Информатика',
            'student_id': self.student.pk,
            'student_name': self.student.full_name,
            'answer_text': 'Ответ',
            'file_url': '/media/homework_submissions/2026/11/26/lab1.pdf',
            'file_name': 'lab1.pdf',
            'submitted_at': item['submitted_at'],
            'status': 'submitted',
            'grade_value': None,
            'teacher_comment': '',
            'checked_at': None,
            'grade_id': None,
        })
        self.assertTrue(item['submitted_at'].endswith('Z'))
        self.assertEqual(self.queue(status='checked').data['submissions'], [])
        self.assertEqual(self.queue(status='invalid').status_code, 400)

        self.client.force_authenticate(self.admin)
        response = self.queue(status='all')
        self.assertEqual(response.data['counts']['all'], 2)
        self.assertEqual(len(response.data['submissions']), 2)
        response = self.queue(assignment_id=self.other_assignment.pk, status='returned')
        self.assertEqual(response.data['counts']['all'], 1)
        self.assertEqual(response.data['submissions'][0]['id'], self.other_submission.pk)

    def test_permissions_cover_review_queue_and_export(self):
        export_url = reverse('journal-export')
        self.assertEqual(self.queue(assignment_id=self.other_assignment.pk).status_code, 404)
        self.assertEqual(
            self.review(self.other_submission, status='checked', grade_value=4).status_code, 404
        )
        self.assertEqual(self.client.get(
            export_url, {**self.week, 'assignment_id': self.other_assignment.pk}
        ).status_code, 404)
        self.client.force_authenticate(self.student)
        self.assertEqual(self.queue().status_code, 403)
        self.assertEqual(self.review(status='checked', grade_value=4).status_code, 403)
        self.assertEqual(self.client.get(export_url, self.week).status_code, 403)

    def test_review_creates_grade_visible_in_weekly_journal(self):
        response = self.review(status='checked', grade_value=4, teacher_comment='Хорошо')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['counts'], {
            'submitted': 0, 'checked': 1, 'returned': 0, 'all': 1,
        })
        self.submission.refresh_from_db()
        grade = Grade.objects.get(pk=response.data['submission']['grade_id'])
        self.assertEqual(self.submission.grade, grade)
        self.assertEqual(grade.assignment, self.assignment)
        self.assertEqual(grade.lesson_date, self.deadline)
        self.assertEqual(grade.teacher, self.teacher)
        self.assertEqual(grade.student, self.student)
        self.assertEqual(grade.subject, self.assignment.subject)
        self.assertEqual(grade.comment, 'Хорошо')
        self.assertTrue(response.data['submission']['checked_at'].endswith('Z'))
        grid = self.client.get(reverse('journal-grid'), self.week)
        cell = grid.data['students'][0]['cells'][self.deadline.isoformat()]
        self.assertEqual(cell['grade']['id'], grade.pk)
        self.assertEqual(cell['grade']['value'], 4)
        self.assertFalse(GradeAuditLog.objects.exists())

    def test_rereview_updates_existing_grade_and_audits_change(self):
        # An older submission already has a grade outside the weekly journal.
        grade = Grade.objects.create(
            student=self.student, subject=self.assignment.subject,
            teacher=self.teacher, value=4, comment='До',
        )
        self.submission.grade = grade
        self.submission.save(update_fields=['grade'])
        self.client.force_authenticate(self.admin)
        payload = {
            'status': 'checked', 'grade_value': 5,
            'teacher_comment': 'После', 'audit_reason': 'Перепроверка',
        }
        response = self.review(**payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['submission']['grade_id'], grade.pk)
        self.assertEqual(self.review(**payload).status_code, 200)
        grade.refresh_from_db()
        self.assertEqual(grade.teacher, self.admin)
        self.assertEqual(grade.lesson_date, self.deadline)
        self.assertEqual(grade.assignment, self.assignment)
        self.assertEqual(Grade.objects.count(), 1)
        entry = GradeAuditLog.objects.get()
        self.assertEqual(entry.grade_id, grade.pk)
        self.assertEqual(entry.changed_by, self.admin)
        self.assertEqual((entry.old_value, entry.new_value), (4, 5))
        self.assertEqual((entry.old_comment, entry.new_comment), ('До', 'После'))
        self.assertEqual(entry.reason, 'Перепроверка')

    def test_return_for_revision_preserves_previously_linked_grade(self):
        self.assertEqual(self.review(status='checked', grade_value=4).status_code, 200)
        response = self.review(status='returned', grade_value=None, teacher_comment='Доработай')
        self.assertEqual(response.status_code, 200)
        submission = response.data['submission']
        self.assertEqual(submission['status'], 'returned')
        self.assertIsNone(submission['grade_value'])
        self.assertEqual(submission['teacher_comment'], 'Доработай')
        self.assertEqual(response.data['counts']['returned'], 1)
        self.assertEqual(Grade.objects.get(pk=submission['grade_id']).value, 4)
        self.assertFalse(GradeAuditLog.objects.exists())

    def test_invalid_and_conflicting_reviews_leave_submission_unchanged(self):
        for fields in ({}, {'grade_value': None}, {'grade_value': 6}):
            self.assertEqual(self.review(status='checked', **fields).status_code, 400)
        grade = Grade.objects.create(
            assignment=self.assignment, lesson_date=self.deadline,
            student=self.student, subject=self.assignment.subject,
            teacher=self.teacher, value=3,
        )
        self.assertEqual(self.review(status='checked', grade_value=4).status_code, 409)
        self.submission.refresh_from_db()
        grade.refresh_from_db()
        self.assertEqual(self.submission.status, 'submitted')
        self.assertIsNone(self.submission.grade_id)
        self.assertEqual(grade.value, 3)
        self.assertFalse(GradeAuditLog.objects.exists())

    def test_export_contains_weekly_grades_attendance_and_numeric_totals(self):
        self.assertEqual(self.review(status='checked', grade_value=4).status_code, 200)
        Attendance.objects.create(
            assignment=self.assignment, student=self.student, date=self.deadline, status='absent'
        )
        Attendance.objects.create(
            assignment=self.assignment, student=self.student,
            date=date(2026, 11, 23), status='present',
        )
        response = self.client.get(reverse('journal-export'), self.week)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'],
                         'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        self.assertEqual(response['Content-Disposition'],
                         f'attachment; filename="journal_{self.assignment.pk}_2026-11-23.xlsx"')
        workbook = load_workbook(BytesIO(b''.join(response.streaming_content)))
        self.addCleanup(workbook.close)
        sheet = workbook.active
        headers, row = list(sheet.values)
        self.assertEqual(headers, (
            'Студент', '2026-11-23', '2026-11-24', '2026-11-25', '2026-11-26',
            '2026-11-27', '2026-11-28', 'Средний балл', 'Посещаемость %',
        ))
        self.assertEqual(row, ('=2+2', 'П', None, None, '4 / Н', None, None, 4, 0.5))
        self.assertEqual(sheet['A2'].data_type, 's')
        self.assertEqual(sheet['I2'].number_format, '0.00%')
