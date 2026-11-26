from datetime import date, time, timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from academic.models import Attendance, Schedule, StudyGroup, TeachingAssignment
from grades.models import Grade, GradeAuditLog
from subjects.models import Subject
from users.models import User


class JournalAPITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.group = StudyGroup.objects.create(name='ИС-21')
        cls.other_group = StudyGroup.objects.create(name='ИС-22')
        cls.teacher = User.objects.create_user(username='teacher', role='teacher')
        cls.other_teacher = User.objects.create_user(username='other_teacher', role='teacher')
        cls.admin = User.objects.create_user(username='admin', role='admin')
        cls.student = User.objects.create_user(username='student', group=cls.group)
        cls.other_student = User.objects.create_user(username='other_student', group=cls.other_group)
        cls.subject = Subject.objects.create(name='Математика')
        cls.assignment = TeachingAssignment.objects.create(
            teacher=cls.teacher, subject=cls.subject, group=cls.group
        )
        cls.other_assignment = TeachingAssignment.objects.create(
            teacher=cls.other_teacher, subject=cls.subject, group=cls.group
        )
        cls.monday = '2026-11-23'

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.teacher)

    def save_cell(self, **fields):
        payload = {
            'assignment_id': self.assignment.pk,
            'student_id': self.student.pk,
            'date': self.monday,
            **fields,
        }
        return self.client.post(reverse('journal-cell'), payload, format='json')

    def grid(self, **params):
        return self.client.get(reverse('journal-grid'), {
            'assignment_id': self.assignment.pk,
            **params,
        })

    def history(self, grade_id):
        return self.client.get(reverse('journal-grade-history', args=[grade_id]))

    def test_teacher_only_has_access_to_own_assignments_and_students(self):
        response = self.client.get(reverse('journal-assignments'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['assignments'], [{
            'id': self.assignment.pk,
            'group_id': self.group.pk,
            'group_name': self.group.name,
            'subject_id': self.subject.pk,
            'subject_name': self.subject.name,
            'teacher_id': self.teacher.pk,
            'teacher_name': self.teacher.full_name,
        }])
        self.assertEqual(self.grid(assignment_id=self.other_assignment.pk).status_code, 404)
        self.assertEqual(
            self.save_cell(assignment_id=self.other_assignment.pk, grade_value=4).status_code, 404
        )
        self.assertEqual(
            self.save_cell(student_id=self.other_student.pk, grade_value=4).status_code, 404
        )
        self.assertFalse(Grade.objects.exists())

        grade_id = self.save_cell(grade_value=4).data['cell']['grade']['id']
        self.save_cell(grade_value=5)
        self.client.force_authenticate(user=self.other_teacher)
        self.assertEqual(self.history(grade_id).status_code, 404)
        self.assertEqual(self.client.patch(
            reverse('grade-detail', args=[grade_id]), {'value': 1}, format='json'
        ).status_code, 403)
        self.assertEqual(Grade.objects.get(pk=grade_id).value, 5)

    def test_student_is_forbidden_on_all_journal_routes(self):
        self.client.force_authenticate(user=self.student)
        self.assertEqual(self.client.get(reverse('journal-assignments')).status_code, 403)
        self.assertEqual(self.grid().status_code, 403)
        self.assertEqual(self.save_cell(grade_value=4).status_code, 403)
        self.assertEqual(self.history(1).status_code, 403)

    def test_admin_has_all_assignments_and_is_recorded_as_editor(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse('journal-assignments'))
        self.assertEqual(
            {item['id'] for item in response.data['assignments']},
            {self.assignment.pk, self.other_assignment.pk},
        )
        self.assertEqual(self.grid().status_code, 200)
        response = self.save_cell(grade_value=4)
        self.assertEqual(response.status_code, 200)
        grade = response.data['cell']['grade']
        self.assertEqual(grade['teacher_name'], self.teacher.full_name)
        self.assertEqual(self.save_cell(grade_value=5).status_code, 200)
        self.assertEqual(self.history(grade['id']).data['history'][0]['changed_by_name'], 'admin')

    def test_week_grid_and_assignment_statistics(self):
        Schedule.objects.create(
            assignment=self.assignment, day=1, start_time=time(8, 30), end_time=time(10)
        )
        self.assertEqual(self.save_cell(grade_value=5, attendance_status='present').status_code, 200)
        self.assertEqual(self.save_cell(
            date='2026-11-16', grade_value=4, attendance_status='absent'
        ).status_code, 200)
        # Legacy and other-assignment grades have no cell in this grid.
        Grade.objects.create(student=self.student, subject=self.subject, value=1)
        Grade.objects.create(
            assignment=self.other_assignment, student=self.student, subject=self.subject,
            value=1, lesson_date=date.fromisoformat(self.monday),
        )
        response = self.grid(week_start=self.monday)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['week_end'], '2026-11-28')
        self.assertEqual(response.data['prev_week'], '2026-11-16')
        self.assertEqual(response.data['next_week'], '2026-11-30')
        self.assertEqual(len(response.data['dates']), 6)
        self.assertEqual(response.data['dates'][0], {
            'date': self.monday, 'weekday': 1, 'label': 'Пн 23.11',
            'has_lesson': True, 'lesson_time': '08:30–10:00',
        })
        student, = response.data['students']
        self.assertEqual(student['avg_grade'], 4.5)
        self.assertEqual(student['attendance_rate'], 50.0)
        self.assertEqual(student['cells'][self.monday]['grade']['value'], 5)
        self.assertEqual(student['cells']['2026-11-28'], {'grade': None, 'attendance': None})
        today = timezone.localdate()
        self.assertEqual(self.grid().data['week_start'], (
            today - timedelta(days=today.weekday())
        ).isoformat())

    def test_grade_and_attendance_are_updated_independently(self):
        self.assertEqual(self.save_cell(grade_value=4, grade_comment='Работа').status_code, 200)
        response = self.save_cell(attendance_status='absent', attendance_comment='Пропуск')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['cell']['grade']['value'], 4)
        self.assertEqual(response.data['cell']['grade']['comment'], 'Работа')
        self.assertEqual(response.data['cell']['attendance']['status'], 'absent')
        self.assertEqual(response.data['attendance_rate'], 0.0)
        self.assertEqual(response.data['avg_grade'], 4.0)

        response = self.save_cell(grade_value=5)
        self.assertEqual(response.data['cell']['attendance']['comment'], 'Пропуск')
        self.assertEqual(Attendance.objects.get().status, 'absent')
        self.assertEqual(response.data['avg_grade'], 5.0)

        response = self.save_cell(attendance_status='late')
        self.assertEqual(response.data['attendance_rate'], 100.0)
        self.assertEqual(response.data['cell']['attendance']['comment'], 'Пропуск')
        response = self.save_cell(attendance_status='')
        self.assertIsNone(response.data['cell']['attendance'])
        self.assertEqual(response.data['cell']['grade']['value'], 5)

    def test_grade_audit_for_value_comment_and_deletion(self):
        grade_id = self.save_cell(grade_value=4, grade_comment='До').data['cell']['grade']['id']
        self.assertEqual(self.history(grade_id).data['history'], [])
        response = self.save_cell(grade_value=5, grade_comment='После', audit_reason='Пересдача')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['cell']['grade']['audit_count'], 1)
        self.assertTrue(response.data['cell']['grade']['updated_at'].endswith('Z'))
        self.save_cell(grade_value=5)
        audit = GradeAuditLog.objects.get()
        self.assertEqual(audit.changed_by, self.teacher)
        self.assertEqual((audit.old_value, audit.new_value), (4, 5))
        self.assertEqual((audit.old_comment, audit.new_comment), ('До', 'После'))
        self.assertEqual(audit.reason, 'Пересдача')

        self.assertEqual(self.save_cell(grade_comment='Исправлен комментарий').status_code, 200)
        response = self.save_cell(grade_value=None, attendance_status='present')
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data['cell']['grade'])
        self.assertEqual(response.data['cell']['attendance']['status'], 'present')
        self.assertEqual(response.data['avg_grade'], 0.0)
        self.assertFalse(Grade.objects.filter(pk=grade_id).exists())
        history = self.history(grade_id).data['history']
        self.assertEqual([(row['old_value'], row['new_value']) for row in history], [
            (5, None), (5, 5), (4, 5)
        ])
        self.assertEqual(history[1]['new_comment'], 'Исправлен комментарий')
        self.assertTrue(history[0]['changed_at'].endswith('Z'))
        self.save_cell(grade_value=3)
        self.assertIsNone(self.save_cell(delete_grade=True).data['cell']['grade'])

    def test_invalid_cell_data_leaves_both_fields_unchanged(self):
        response = self.save_cell(grade_value=6, attendance_status='present')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Attendance.objects.exists())
        self.assertFalse(Grade.objects.exists())
        self.assertEqual(self.grid(week_start='2026-11-24').status_code, 400)
        self.assertEqual(self.grid(week_start='0001-01-01').status_code, 400)

    def test_session_authentication_enforces_csrf_and_jwt_also_works(self):
        self.client = APIClient(enforce_csrf_checks=True)
        self.client.force_login(self.teacher)
        self.assertEqual(self.grid().status_code, 200)
        self.assertEqual(self.save_cell(grade_value=4).status_code, 403)

        csrf_token = 'a' * 32
        self.client.cookies['csrftoken'] = csrf_token
        self.client.credentials(HTTP_X_CSRFTOKEN=csrf_token)
        self.assertEqual(self.save_cell(grade_value=4).status_code, 200)

        self.client.logout()
        token = RefreshToken.for_user(self.teacher).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        self.assertEqual(self.save_cell(grade_value=5).status_code, 200)
