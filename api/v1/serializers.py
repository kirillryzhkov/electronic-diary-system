# api/v1/serializers.py
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


from users.models import User
from subjects.models import Subject
from grades.models import Grade


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role']
        read_only_fields = ['id']


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['id', 'name', 'description']

class GradeSerializer(serializers.ModelSerializer):
    student = UserSerializer(read_only=True)
    teacher = UserSerializer(read_only=True)
    subject = SubjectSerializer(read_only=True)

    class Meta:
        model = Grade
        fields = ['id', 'student', 'teacher', 'subject', 'value', 'comment', 'date']
        read_only_fields = ['id', 'student', 'teacher', 'subject', 'date']

    def validate_value(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError('Оценка должна быть от 1 до 5.')
        return value


class GradeCreateSerializer(serializers.ModelSerializer):
    student = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role='student')
    )

    class Meta:
        model = Grade
        fields = ['student', 'subject', 'value', 'comment']

    def validate_value(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError('Оценка должна быть от 1 до 5.')
        return value

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