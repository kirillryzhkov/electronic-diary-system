# api/v1/views.py
from django.db.models import Avg, Count
from rest_framework import filters, generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from subjects.models import Subject
from grades.models import Grade
from .serializers import (
    SubjectSerializer,
    GradeSerializer,
    GradeCreateSerializer,
    StudentAverageSerializer,
    SubjectStatisticsSerializer,
)
from .permissions import (
    IsTeacher,
    IsGradeOwnerOrTeacher,
)

@extend_schema(
    tags=['Предметы'],
    summary='Список и создание предметов',
    description='Позволяет получить список предметов и создать новый предмет. Создание доступно только учителю.',
)
class SubjectListCreateView(generics.ListCreateAPIView):
    serializer_class = SubjectSerializer

    def get_permissions(self):
        # Смотреть список предметов может любой авторизованный пользователь,
        # создавать предметы может только учитель.
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsTeacher()]
        return [IsAuthenticated()]

    def get_queryset(self):
        return Subject.objects.all().order_by('name')

@extend_schema(
    tags=['Статистика'],
    summary='Статистика по предметам',
    description='Возвращает количество оценок и средний балл по каждому предмету.',
)
class SubjectStatisticsView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsTeacher]
    serializer_class = SubjectStatisticsSerializer

    def get(self, request):
        subjects = Subject.objects.annotate(
            avg=Avg('grades__value'),
            total=Count('grades')
        ).order_by('name')

        stats = [
            {
                'subject': subject.name,
                'total_grades': subject.total,
                'average': round(subject.avg or 0, 2)
            }
            for subject in subjects
        ]

        return Response(stats, status=status.HTTP_200_OK)

@extend_schema(
    tags=['Оценки'],
    summary='Получить список оценок',
    description='Учитель видит все оценки. Ученик видит только свои оценки.',
)
class GradeListView(generics.ListAPIView):
    serializer_class = GradeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['student__username', 'subject__name']
    ordering_fields = ['date', 'value']
    ordering = ['-date']

    def get_queryset(self):
        user = self.request.user
        queryset = Grade.objects.select_related('student', 'subject').all()

        # Ученик видит только свои оценки.
        if user.role == 'student':
            queryset = queryset.filter(student=user)

        # Фильтрация по предмету: /api/v1/grades/?subject=1
        subject_id = self.request.query_params.get('subject')
        if subject_id:
            try:
                queryset = queryset.filter(subject_id=int(subject_id))
            except ValueError:
                queryset = queryset.none()

        return queryset.order_by('-date', '-id')

@extend_schema(
    tags=['Оценки'],
    summary='Просмотр, изменение или удаление оценки',
    description='Учитель может изменять и удалять оценки. Ученик может только просматривать свои оценки.',
)
class GradeDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = GradeSerializer
    permission_classes = [IsAuthenticated, IsGradeOwnerOrTeacher]

    def get_queryset(self):
        # Не фильтруем queryset по студенту, чтобы чужая оценка возвращала 403,
        # а не 404. Доступ проверяет IsGradeOwnerOrTeacher.
        return Grade.objects.select_related('student', 'subject').all()

@extend_schema(
    tags=['Оценки'],
    summary='Создать оценку',
    description='Создание оценки доступно только пользователю с ролью teacher.',
)
class GradeCreateView(generics.CreateAPIView):
    serializer_class = GradeCreateSerializer
    permission_classes = [IsAuthenticated, IsTeacher]

    def perform_create(self, serializer):
        serializer.save()

@extend_schema(
    tags=['Статистика'],
    summary='Средний балл ученика',
    description='Возвращает средний балл текущего авторизованного ученика.',
)
class StudentAverageView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = StudentAverageSerializer

    def get(self, request):
        if request.user.role != 'student':
            return Response(
                {'detail': 'Only students can view average.'},
                status=status.HTTP_403_FORBIDDEN
            )

        grades = Grade.objects.filter(student=request.user)

        average = grades.aggregate(avg=Avg('value'))['avg']

        return Response(
            {'average': round(average or 0, 2)},
            status=status.HTTP_200_OK
        )
