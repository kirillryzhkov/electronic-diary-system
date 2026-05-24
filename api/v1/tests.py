# api/v1/tests.py

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from users.models import User
from subjects.models import Subject
from grades.models import Grade


class GradeAPITestCase(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.teacher = User.objects.create_user(
            username='teacher',
            email='teacher@example.com',
            password='password123',
            role='teacher'
        )

        self.student = User.objects.create_user(
            username='student',
            email='student@example.com',
            password='password123',
            role='student'
        )

        self.math_subject = Subject.objects.create(name="Математика")
        self.phys_subject = Subject.objects.create(name="Физика")

        self.grade1 = Grade.objects.create(
            student=self.student,
            subject=self.math_subject,
            value=5
        )
        self.grade2 = Grade.objects.create(
            student=self.student,
            subject=self.phys_subject,
            value=4
        )

    def test_student_can_view_own_grades(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.get(reverse('grade-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_teacher_can_view_all_grades(self):
        self.client.force_authenticate(user=self.teacher)
        response = self.client.get(reverse('grade-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Учитель видит все оценки (в нашем случае 2)
        self.assertEqual(len(response.data['results']), 2)

    def test_student_cannot_view_other_students_grades(self):
        # Создаем второго студента
        student2 = User.objects.create_user(
            username='student2',
            email='student2@example.com',
            password='password123',
            role='student'
        )
        Grade.objects.create(
            student=student2,
            subject=self.math_subject,
            value=3
        )

        self.client.force_authenticate(user=self.student)
        response = self.client.get(reverse('grade-list'))
        # Студент видит только свои оценки
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_grade_filtering_by_subject(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.get(reverse('grade-list') + '?subject=1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Ожидаем одну оценку по математике
        self.assertEqual(len(response.data['results']), 1)

    def test_grade_search(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.get(reverse('grade-list') + '?search=математика')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_student_average_calculation(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.get(reverse('student-average'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['average'], 4.5)

    def test_teacher_can_edit_grade(self):
        self.client.force_authenticate(user=self.teacher)
        response = self.client.put(
            reverse('grade-detail', kwargs={'pk': self.grade1.id}),
            {'value': 3},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.grade1.refresh_from_db()
        self.assertEqual(self.grade1.value, 3)

    def test_student_cannot_edit_other_grades(self):
        # Создаем второго студента
        student2 = User.objects.create_user(
            username='student2',
            email='student2@example.com',
            password='password123',
            role='student'
        )
        grade_of_student2 = Grade.objects.create(
            student=student2,
            subject=self.math_subject,
            value=4
        )

        self.client.force_authenticate(user=self.student)
        response = self.client.put(
            reverse('grade-detail', kwargs={'pk': grade_of_student2.id}),
            {'value': 5},
            format='json'
        )
        # Студент не может редактировать чужие оценки
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_teacher_can_delete_grade(self):
        self.client.force_authenticate(user=self.teacher)
        response = self.client.delete(reverse('grade-detail', kwargs={'pk': self.grade1.id}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Grade.objects.filter(id=self.grade1.id).exists())

    def test_teacher_can_view_subject_statistics(self):
        self.client.force_authenticate(user=self.teacher)
        response = self.client.get(reverse('subject-stats'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
