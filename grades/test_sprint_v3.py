from datetime import date
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from academic.models import Attendance, Homework, HomeworkSubmission, StudyGroup, TeachingAssignment
from grades.models import Grade
from notifications_app.models import Notification
from subjects.models import Subject
from users.models import User


class TelegramProfileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='student')
        self.other_user = User.objects.create_user(username='other', telegram_chat_id='1234')
        self.profile_url = reverse('telegram-profile')
        self.test_url = reverse('telegram-test')
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    @override_settings(TELEGRAM_BOT_TOKEN='')
    def test_profile_defaults_partial_update_validation_and_user_isolation(self):
        self.assertEqual(self.client.get(self.profile_url).data, {
            'telegram_chat_id': '',
            'telegram_notifications_enabled': False,
            'bot_configured': False,
        })
        response = self.client.patch(self.profile_url, {
            'telegram_chat_id': '673739010',
            'telegram_notifications_enabled': True,
            'bot_configured': True,
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['telegram_chat_id'], '673739010')
        self.assertFalse(response.data['bot_configured'])
        response = self.client.patch(
            self.profile_url, {'telegram_notifications_enabled': False}, format='json'
        )
        self.assertEqual(response.data['telegram_chat_id'], '673739010')
        self.assertFalse(response.data['telegram_notifications_enabled'])
        response = self.client.patch(
            self.profile_url, {'telegram_chat_id': 'https://example.test'}, format='json'
        )
        self.assertEqual(response.status_code, 400)
        self.user.refresh_from_db()
        self.other_user.refresh_from_db()
        self.assertEqual(self.user.telegram_chat_id, '673739010')
        self.assertEqual(self.other_user.telegram_chat_id, '1234')
        self.assertEqual(self.client.post(self.test_url).status_code, 400)

    @override_settings(TELEGRAM_BOT_TOKEN='test-token')
    @patch('api.v1.telegram.send_telegram_message', return_value=True)
    def test_test_message_requires_address_and_reports_delivery(self, send):
        self.assertEqual(self.client.post(self.test_url).status_code, 400)
        send.assert_not_called()
        self.client.patch(self.profile_url, {'telegram_chat_id': '673739010'}, format='json')
        self.assertTrue(self.client.get(self.profile_url).data['bot_configured'])
        response = self.client.post(self.test_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'ok': True, 'detail': 'Тестовое уведомление отправлено'})
        send.assert_called_once_with('673739010', 'Тестовое уведомление из электронного дневника.')
        send.return_value = False
        self.assertEqual(self.client.post(self.test_url).status_code, 502)
        self.assertFalse(Notification.objects.exists())

    def test_profile_supports_session_csrf_and_jwt(self):
        client = APIClient(enforce_csrf_checks=True)
        self.assertEqual(client.get(self.profile_url).status_code, 401)
        client.force_login(self.user)
        self.assertEqual(client.get(self.profile_url).status_code, 200)
        payload = {'telegram_chat_id': '673739010'}
        self.assertEqual(client.patch(self.profile_url, payload, format='json').status_code, 403)
        csrf_token = 'a' * 32
        client.cookies['csrftoken'] = csrf_token
        client.credentials(HTTP_X_CSRFTOKEN=csrf_token)
        self.assertEqual(client.patch(self.profile_url, payload, format='json').status_code, 200)
        client.logout()
        token = RefreshToken.for_user(self.user).access_token
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        self.assertEqual(client.get(self.profile_url).status_code, 200)


class SprintV3DataTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.group = StudyGroup.objects.create(name='ИС-31')
        cls.other_group = StudyGroup.objects.create(name='ИС-32')
        cls.teacher = User.objects.create_user(username='teacher', role='teacher')
        other_teacher = User.objects.create_user(username='other_teacher', role='teacher')
        cls.admin = User.objects.create_user(username='admin', role='admin')
        cls.student = User.objects.create_user(username='student', group=cls.group)
        cls.empty_student = User.objects.create_user(username='empty', group=cls.group)
        cls.other_student = User.objects.create_user(username='other_student', group=cls.other_group)
        cls.subject = Subject.objects.create(name='Информатика')
        cls.other_subject = Subject.objects.create(name='Математика')
        cls.assignment = TeachingAssignment.objects.create(
            teacher=cls.teacher, group=cls.group, subject=cls.subject,
        )
        cls.parallel_assignment = TeachingAssignment.objects.create(
            teacher=other_teacher, group=cls.group, subject=cls.subject,
        )
        cls.other_assignment = TeachingAssignment.objects.create(
            teacher=other_teacher, group=cls.other_group, subject=cls.other_subject,
        )
        cls.day = date(2026, 11, 26)
        cls.homework = Homework.objects.create(
            assignment=cls.assignment, title='Лабораторная', deadline=cls.day,
        )

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.teacher)

    def save_cell(self, **changes):
        return self.client.post(reverse('journal-cell'), {
            'assignment_id': self.assignment.pk,
            'student_id': self.student.pk,
            'date': self.day.isoformat(),
            **changes,
        }, format='json')

    def review(self, submission, **changes):
        return self.client.post(
            reverse('homework-submission-review', args=[submission.pk]), changes, format='json'
        )

    def analytics(self, user):
        self.client.force_authenticate(user)
        response = self.client.get(reverse('analytics-overview'))
        self.assertEqual(response.status_code, 200)
        return response.data

    def test_journal_creates_notifications_only_for_actual_grade_changes_and_absences(self):
        self.assertEqual(self.save_cell(attendance_status='present').status_code, 200)
        self.assertEqual(self.save_cell(grade_value=4, attendance_status='absent').status_code, 200)
        self.assertEqual(self.save_cell(grade_value=4, attendance_status='absent').status_code, 200)
        self.assertEqual(self.save_cell(grade_value=5).status_code, 200)
        self.assertEqual(self.save_cell(delete_grade=True).status_code, 200)
        self.assertEqual(list(self.student.notifications.order_by('pk').values_list(
            'notification_type', 'title'
        )), [
            ('attendance', 'Отмечен пропуск'),
            ('grade', 'Новая оценка'),
            ('grade', 'Оценка изменена'),
        ])
        self.assertFalse(self.teacher.notifications.exists())

    def test_review_and_return_send_homework_notifications_without_duplicates(self):
        submission = HomeworkSubmission.objects.create(homework=self.homework, student=self.student)
        for _ in range(2):
            self.assertEqual(self.review(submission, status='checked', grade_value=5).status_code, 200)
        self.assertEqual(self.review(
            submission, status='returned', teacher_comment='Доработай'
        ).status_code, 200)
        self.assertEqual(list(self.student.notifications.order_by('pk').values_list(
            'notification_type', 'title'
        )), [
            ('homework', 'Домашнее задание проверено'),
            ('homework', 'Домашнее задание возвращено на доработку'),
        ])

    def test_analytics_keeps_data_in_scope_for_all_roles(self):
        self.assertEqual(self.save_cell(grade_value=3, attendance_status='absent').status_code, 200)
        Grade.objects.create(student=self.student, subject=self.subject, teacher=self.teacher, value=2)
        Grade.objects.create(
            student=self.student, subject=self.subject, teacher=self.parallel_assignment.teacher,
            assignment=self.parallel_assignment, lesson_date=self.day, value=5,
        )
        Grade.objects.create(
            student=self.other_student, subject=self.other_subject, teacher=self.other_assignment.teacher,
            assignment=self.other_assignment, lesson_date=self.day, value=5,
        )
        Attendance.objects.create(
            student=self.student, assignment=self.parallel_assignment, date=self.day, status='late',
        )
        HomeworkSubmission.objects.create(homework=self.homework, student=self.student)
        returned = Homework.objects.create(assignment=self.assignment, title='Возврат', deadline=self.day)
        HomeworkSubmission.objects.create(homework=returned, student=self.student, status='returned')
        Homework.objects.create(assignment=self.assignment, title='Ожидает сдачи', deadline=self.day)
        external = Homework.objects.create(
            assignment=self.other_assignment, title='Другая группа', deadline=self.day,
        )
        HomeworkSubmission.objects.create(homework=external, student=self.other_student)

        teacher = self.analytics(self.teacher)
        self.assertEqual(teacher, {
            'role': 'teacher',
            'summary': {
                'students_count': 2, 'risk_count': 1, 'pending_homework': 1, 'avg_grade': 2.5,
            },
            'risk_students': [{
                'student_id': self.student.pk,
                'student_name': self.student.full_name,
                'group_name': self.group.name,
                'avg_grade': 2.5,
                'attendance_rate': 0.0,
                'reasons': ['Низкий ср. балл', 'Низкая посещаемость'],
            }],
            'subjects': [{'subject_name': self.subject.name, 'avg_grade': 2.5, 'grades_count': 2}],
        })
        admin = self.analytics(self.admin)
        self.assertEqual(admin['role'], 'admin')
        self.assertEqual(admin['summary'], {
            'students_count': 3, 'risk_count': 1, 'pending_homework': 2, 'avg_grade': 3.75,
        })
        self.assertEqual(
            admin['risk_students'][0]['reasons'],
            ['Низкий ср. балл', 'Низкая посещаемость'],
        )
        self.assertEqual(len(admin['subjects']), 2)

        student = self.analytics(self.student)
        self.assertEqual(student, {
            'role': 'student',
            'summary': {
                'avg_grade': 3.33, 'attendance_rate': 50.0,
                'unread_notifications': 2, 'pending_homework': 2,
            },
            'subjects': [{'subject_name': self.subject.name, 'avg_grade': 3.33, 'grades_count': 3}],
        })
        self.assertEqual(self.analytics(self.empty_student)['summary']['avg_grade'], 0.0)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(reverse('analytics-overview')).status_code, 401)
