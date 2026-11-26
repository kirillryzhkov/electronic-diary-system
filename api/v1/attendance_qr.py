from datetime import timedelta
from secrets import token_urlsafe

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiTypes
from rest_framework import serializers, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from academic.models import AttendanceQRSession, TeachingAssignment
from .journal import JournalView, utc_timestamp


class QRCreateSerializer(serializers.Serializer):
    assignment_id = serializers.IntegerField(min_value=1, max_value=2**63 - 1)
    date = serializers.DateField()
    ttl_minutes = serializers.IntegerField(min_value=1, max_value=30, default=5)


def student_roster(assignment):
    return assignment.group.students.filter(role='student')


def present_students(session, roster):
    return session.assignment.attendance_records.filter(
        date=session.date, status='present', student__in=roster,
    )


class QRCreateView(JournalView):
    @extend_schema(request=QRCreateSerializer, responses={201: OpenApiTypes.OBJECT})
    @transaction.atomic
    def post(self, request):
        serializer = QRCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        # Share the assignment lock with check-in and manual journal changes.
        assignment = get_object_or_404(
            self.assignments().select_for_update(), pk=data['assignment_id']
        )
        day = data['date']
        assignment.qr_sessions.filter(date=day, is_active=True).update(is_active=False)
        session = assignment.qr_sessions.create(
            token=token_urlsafe(24),
            date=day,
            created_by=request.user,
            expires_at=timezone.now() + timedelta(minutes=data['ttl_minutes']),
        )
        roster = student_roster(assignment)
        return Response({
            'token': session.token,
            'assignment_id': assignment.pk,
            'group_name': assignment.group.name,
            'subject_name': assignment.subject.name,
            'date': day.isoformat(),
            'expires_at': utc_timestamp(session.expires_at),
            'checkin_path': f'/attendance/qr/checkin/{session.token}/',
            'total_students': roster.count(),
            'checked_in_count': present_students(session, roster).count(),
        }, status=status.HTTP_201_CREATED)


class QRStatusView(JournalView):
    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request, token):
        session = get_object_or_404(
            AttendanceQRSession.objects.select_related('assignment'),
            assignment__in=self.assignments(), token=token,
        )
        roster = student_roster(session.assignment)
        students = [
            {'id': mark.student_id, 'full_name': mark.student.full_name, 'status': mark.status}
            for mark in present_students(session, roster).select_related('student').order_by(
                'student__last_name', 'student__first_name', 'student_id'
            )
        ]
        response = Response({
            'token': session.token,
            'is_active': session.is_active,
            'is_expired': timezone.now() > session.expires_at,
            'expires_at': utc_timestamp(session.expires_at),
            'total_students': roster.count(),
            'checked_in_count': len(students),
            'checked_in_students': students,
        })
        response['Cache-Control'] = 'no-store'
        return response


class QRCloseView(JournalView):
    @extend_schema(request=None, responses=OpenApiTypes.OBJECT)
    def post(self, request, token):
        updated = AttendanceQRSession.objects.filter(
            assignment__in=self.assignments(), token=token,
        ).update(is_active=False)
        if not updated:
            return Response({'detail': 'QR-код не найден.'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'ok': True, 'is_active': False})


class QRCheckinView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses={200: OpenApiTypes.OBJECT, 410: OpenApiTypes.OBJECT})
    @transaction.atomic
    def post(self, request, token):
        student = request.user
        if student.role != 'student':
            raise PermissionDenied('Отметиться по QR могут только студенты.')

        session = get_object_or_404(AttendanceQRSession, token=token)
        assignment = get_object_or_404(
            TeachingAssignment.objects.select_for_update(), pk=session.assignment_id,
        )
        if student.group_id != assignment.group_id:
            raise PermissionDenied('QR-код относится к другой группе.')
        # Reload under the row lock so rotation or closure cannot race with check-in.
        session = get_object_or_404(AttendanceQRSession.objects.select_for_update(), pk=session.pk)
        if not session.is_active or timezone.now() > session.expires_at:
            return Response(
                {'detail': 'QR-код недействителен или истёк'}, status=status.HTTP_410_GONE,
            )

        attendance, created = assignment.attendance_records.get_or_create(
            student=student, date=session.date, defaults={'status': 'present'}
        )
        already_checked_in = not created and attendance.status == 'present'
        if not created and not already_checked_in:
            attendance.status = 'present'
            attendance.save(update_fields=['status'])

        return Response({
            'ok': True,
            'status': 'present',
            'already_checked_in': already_checked_in,
            'subject_name': assignment.subject.name,
            'group_name': assignment.group.name,
            'date': session.date.isoformat(),
            'detail': 'Присутствие отмечено!',
        })
