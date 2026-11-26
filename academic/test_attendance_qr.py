from datetime import date, timedelta
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from academic.models import Attendance, AttendanceQRSession, StudyGroup, TeachingAssignment
from grades.models import Grade
from subjects.models import Subject
from users.models import User


class AttendanceQRTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.group = StudyGroup.objects.create(name='ИС-31')
        other_group = StudyGroup.objects.create(name='ПО-22')
        cls.teacher = User.objects.create_user(username='teacher', role='teacher')
        cls.other_teacher = User.objects.create_user(username='other_teacher', role='teacher')
        cls.admin = User.objects.create_user(username='admin', role='admin')
        cls.student = User.objects.create_user(username='student', group=cls.group)
        cls.second_student = User.objects.create_user(username='second', group=cls.group)
        cls.other_student = User.objects.create_user(username='other_student', group=other_group)
        cls.subject = Subject.objects.create(name='Информатика')
        cls.assignment = TeachingAssignment.objects.create(
            teacher=cls.teacher, group=cls.group, subject=cls.subject,
        )
        cls.day = date(2026, 11, 26)

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.teacher)

    def create_qr(self, **changes):
        return self.client.post(reverse('attendance-qr-create'), {
            'assignment_id': self.assignment.pk, 'date': self.day.isoformat(), **changes,
        }, format='json')

    def qr_url(self, action, token):
        return reverse(f'attendance-qr-{action}', args=[token])

    def session_token(self):
        response = self.create_qr()
        self.assertEqual(response.status_code, 201)
        return response.data['token']

    def test_create_sets_ttl_and_rotates_only_matching_assignment_and_day(self):
        fixed_now = timezone.now()
        with patch('api.v1.attendance_qr.timezone.now', return_value=fixed_now):
            response = self.create_qr()
        self.assertEqual(response.status_code, 201)
        token = response.data['token']
        self.assertRegex(token, r'\A[A-Za-z0-9_-]{32}\Z')
        session = AttendanceQRSession.objects.get(token=token)
        self.assertEqual(session.expires_at, fixed_now + timedelta(minutes=5))
        self.assertEqual(session.created_by, self.teacher)
        self.assertEqual(response.data, {
            'token': token,
            'assignment_id': self.assignment.pk,
            'group_name': self.group.name,
            'subject_name': self.subject.name,
            'date': self.day.isoformat(),
            'expires_at': session.expires_at.isoformat().replace('+00:00', 'Z'),
            'checkin_path': f'/attendance/qr/checkin/{token}/',
            'total_students': 2,
            'checked_in_count': 0,
        })

        other_day = (self.day + timedelta(days=1)).isoformat()
        token_other_day = self.create_qr(date=other_day, ttl_minutes=30).data['token']
        for ttl in (0, 31):
            self.assertEqual(self.create_qr(ttl_minutes=ttl).status_code, 400)
        self.assertTrue(AttendanceQRSession.objects.get(pk=session.pk).is_active)
        self.assertNotEqual(self.session_token(), token)
        session.refresh_from_db()
        self.assertFalse(session.is_active)
        self.assertTrue(AttendanceQRSession.objects.get(token=token_other_day).is_active)

    def test_staff_access_and_student_permissions(self):
        token = self.session_token()
        status_url = self.qr_url('status', token)
        close_url = self.qr_url('close', token)
        self.client.force_authenticate(self.other_teacher)
        self.assertEqual(self.create_qr().status_code, 404)
        self.assertEqual(self.client.get(status_url).status_code, 404)
        self.assertEqual(self.client.post(close_url).status_code, 404)
        self.assertEqual(self.client.post(self.qr_url('checkin', token)).status_code, 403)

        self.client.force_authenticate(self.student)
        self.assertEqual(self.create_qr().status_code, 403)
        self.assertEqual(self.client.get(status_url).status_code, 403)
        self.assertEqual(self.client.post(close_url).status_code, 403)

        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.get(status_url).status_code, 200)
        self.assertEqual(self.client.post(close_url).data, {'ok': True, 'is_active': False})
        self.assertEqual(self.client.post(close_url).status_code, 200)
        self.assertEqual(self.create_qr().status_code, 201)

    def test_checkin_updates_attendance_without_touching_grade_and_is_repeatable(self):
        mark = Attendance.objects.create(
            student=self.student, assignment=self.assignment, date=self.day,
            status='absent', comment='Комментарий преподавателя',
        )
        grade = Grade.objects.create(
            student=self.student, teacher=self.teacher, subject=self.subject,
            assignment=self.assignment, lesson_date=self.day, value=5,
        )
        grade_snapshot = Grade.objects.values().get(pk=grade.pk)
        token = self.session_token()
        url = self.qr_url('checkin', token)
        self.client.force_authenticate(self.student)
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {
            'ok': True, 'status': 'present', 'already_checked_in': False,
            'subject_name': self.subject.name, 'group_name': self.group.name,
            'date': self.day.isoformat(), 'detail': 'Присутствие отмечено!',
        })
        mark.refresh_from_db()
        self.assertEqual(mark.status, 'present')
        self.assertEqual(mark.comment, 'Комментарий преподавателя')
        self.assertTrue(self.client.post(url).data['already_checked_in'])
        self.client.force_authenticate(self.second_student)
        self.assertFalse(self.client.post(url).data['already_checked_in'])
        self.assertEqual(Attendance.objects.count(), 2)
        self.assertEqual(Grade.objects.values().get(pk=grade.pk), grade_snapshot)

        self.client.force_authenticate(self.teacher)
        status_data = self.client.get(self.qr_url('status', token)).data
        self.assertTrue(status_data['is_active'])
        self.assertFalse(status_data['is_expired'])
        self.assertEqual(status_data['checked_in_count'], 2)
        self.assertEqual(status_data['total_students'], 2)
        self.assertIn({
            'id': self.student.pk, 'full_name': self.student.full_name, 'status': 'present',
        }, status_data['checked_in_students'])

    def test_checkin_rejects_other_group_missing_closed_and_expired_tokens(self):
        closed = self.session_token()
        self.assertEqual(self.client.post(self.qr_url('close', closed)).status_code, 200)
        expired = self.session_token()
        active = self.create_qr(date='2026-11-27').data['token']
        AttendanceQRSession.objects.filter(token=expired).update(
            expires_at=timezone.now() - timedelta(seconds=1)
        )
        self.assertTrue(self.client.get(self.qr_url('status', expired)).data['is_expired'])
        self.assertFalse(self.client.get(self.qr_url('status', closed)).data['is_active'])

        self.client.force_authenticate(self.other_student)
        self.assertEqual(self.client.post(self.qr_url('checkin', active)).status_code, 403)
        self.client.force_authenticate(self.student)
        for token in (closed, expired):
            response = self.client.post(self.qr_url('checkin', token))
            self.assertEqual(response.status_code, 410)
            self.assertEqual(response.data, {'detail': 'QR-код недействителен или истёк'})
        self.assertEqual(self.client.post(self.qr_url('checkin', 'missing')).status_code, 404)
        self.assertFalse(Attendance.objects.exists())

    def test_checkin_supports_session_csrf_and_jwt(self):
        url = self.qr_url('checkin', self.session_token())
        client = APIClient(enforce_csrf_checks=True)
        self.assertEqual(client.post(url).status_code, 401)
        client.force_login(self.student)
        self.assertEqual(client.post(url).status_code, 403)
        csrf_token = 'a' * 32
        client.cookies['csrftoken'] = csrf_token
        client.credentials(HTTP_X_CSRFTOKEN=csrf_token)
        self.assertEqual(client.post(url).status_code, 200)
        client.logout()
        token = RefreshToken.for_user(self.student).access_token
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        self.assertEqual(client.post(url).status_code, 200)
