from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import User, StudentProfile
from apps.academic.models import Grade


class StudentRegistrationTestCase(APITestCase):
    def setUp(self):
        # Test uchun sinf yaratish
        self.grade = Grade.objects.create(name="7-sinf")

    def test_student_registration_success(self):
        """Muvaffaqiyatli student registratsiyasi"""
        url = reverse('student-register')
        data = {
            'first_name': 'Ali',
            'last_name': 'Valiyev',
            'grade_id': str(self.grade.id),
            'email': 'ali@example.com',
            'password': 'testpassword123'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user', response.data)
        self.assertIn('tokens', response.data)

        # User yaratilganligini tekshirish
        user = User.objects.get(email='ali@example.com')
        self.assertEqual(user.first_name, 'Ali')
        self.assertEqual(user.last_name, 'Valiyev')
        self.assertEqual(user.role, User.Role.STUDENT)

        # StudentProfile yaratilganligini tekshirish
        profile = StudentProfile.objects.get(user=user)
        self.assertEqual(profile.grade, self.grade)

    def test_student_registration_duplicate_email(self):
        """Takroriy email bilan registratsiya"""
        # Avval user yaratish
        User.objects.create_user(
            username='existing@example.com',
            email='existing@example.com',
            password='password123'
        )

        url = reverse('student-register')
        data = {
            'first_name': 'Ali',
            'last_name': 'Valiyev',
            'grade_id': str(self.grade.id),
            'email': 'existing@example.com',
            'password': 'testpassword123'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_student_registration_invalid_grade(self):
        """Noto'g'ri sinf ID bilan registratsiya"""
        url = reverse('student-register')
        data = {
            'first_name': 'Ali',
            'last_name': 'Valiyev',
            'grade_id': 'invalid-uuid',
            'email': 'ali@example.com',
            'password': 'testpassword123'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('grade_id', response.data)