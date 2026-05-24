# api/v1/serializers.py
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


from users.models import User
from subjects.models import Subject
from grades.models import Grade


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'full_name', 'email', 'role']
        read_only_fields = ['id']


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['id', 'name', 'description']

class GradeSerializer(serializers.ModelSerializer):
    student = UserSerializer(read_only=True)
    subject = SubjectSerializer(read_only=True)
    period_label = serializers.CharField(read_only=True)

    class Meta:
        model = Grade
        fields = [
            'id',
            'student',
            'subject',
            'value',
            'comment',
            'grade_type',
            'month',
            'semester',
            'period_label',
            'date',
        ]
        read_only_fields = ['id', 'student', 'subject', 'date', 'period_label']

    def validate(self, attrs):
        value = attrs.get('value')
        grade_type = attrs.get('grade_type')
        month = attrs.get('month')
        semester = attrs.get('semester')

        if value < 1 or value > 5:
            raise serializers.ValidationError('Оценка должна быть от 1 до 5.')

        if grade_type == 'monthly' and not month:
            raise serializers.ValidationError('Для месячной аттестации нужно указать месяц.')

        if grade_type in ['semester', 'exam'] and not semester:
            raise serializers.ValidationError('Для сессии и экзамена нужно указать полугодие.')

        return attrs


class GradeCreateSerializer(serializers.ModelSerializer):
    student = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role='student')
    )

    class Meta:
        model = Grade
        fields = [
            'student',
            'subject',
            'value',
            'comment',
            'grade_type',
            'month',
            'semester',
        ]

    def validate(self, attrs):
        value = attrs.get('value')
        grade_type = attrs.get('grade_type')
        month = attrs.get('month')
        semester = attrs.get('semester')

        if value < 1 or value > 5:
            raise serializers.ValidationError('Оценка должна быть от 1 до 5.')

        if grade_type == 'monthly' and not month:
            raise serializers.ValidationError('Для месячной аттестации нужно указать месяц.')

        if grade_type in ['semester', 'exam'] and not semester:
            raise serializers.ValidationError('Для сессии и экзамена нужно указать полугодие.')

        return attrs

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = user.role
        token['username'] = user.username
        return token





class StudentAverageSerializer(serializers.Serializer):
    average = serializers.FloatField()


class SubjectStatisticsSerializer(serializers.Serializer):
    subject = serializers.CharField()
    total_grades = serializers.IntegerField()
    average = serializers.FloatField()