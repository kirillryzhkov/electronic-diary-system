from datetime import date, timedelta

from rest_framework import serializers

from academic.models import Attendance


class JournalQuerySerializer(serializers.Serializer):
    assignment_id = serializers.IntegerField(min_value=1, max_value=2**63 - 1)
    week_start = serializers.DateField(required=False)

    def validate_week_start(self, value):
        if value.weekday() != 0:
            raise serializers.ValidationError('Укажи понедельник.')
        if not date.min + timedelta(days=7) <= value <= date.max - timedelta(days=7):
            raise serializers.ValidationError('Неделя выходит за допустимый диапазон дат.')
        return value


class JournalCellSerializer(serializers.Serializer):
    assignment_id = serializers.IntegerField(min_value=1, max_value=2**63 - 1)
    student_id = serializers.IntegerField(min_value=1, max_value=2**63 - 1)
    date = serializers.DateField()
    attendance_status = serializers.ChoiceField(
        choices=Attendance.STATUS_CHOICES, allow_blank=True, required=False
    )
    attendance_comment = serializers.CharField(
        allow_blank=True, required=False, trim_whitespace=False
    )
    grade_value = serializers.IntegerField(min_value=1, max_value=5, allow_null=True, required=False)
    grade_comment = serializers.CharField(allow_blank=True, required=False, trim_whitespace=False)
    delete_grade = serializers.BooleanField(required=False)
    audit_reason = serializers.CharField(allow_blank=True, required=False)
