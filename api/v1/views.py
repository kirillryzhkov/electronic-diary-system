from django.db.models import Avg, Count
from rest_framework import filters, generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

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


@extend_schema_view(
    get=extend_schema(
        tags=['Предметы'],
        summary='Получить список предметов',
        description='Возвращает список всех предметов.',
    ),
    post=extend_schema(
        tags=['Предметы'],
        summary='Создать предмет',
        description='Создаёт новый предмет. Доступно только преподавателю.',
    ),
)
class SubjectListCreateView(generics.ListCreateAPIView):
    serializer_class = SubjectSerializer

    def get_permissions(self):
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
    parameters=[
        OpenApiParameter(
            name='subject',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='ID предмета для фильтрации'
        ),
        OpenApiParameter(
            name='search',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Поиск по логину ученика или названию предмета'
        ),
        OpenApiParameter(
            name='ordering',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Сортировка: date, -date, value, -value'
        ),
    ],
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

        if user.role == 'student':
            queryset = queryset.filter(student=user)

        subject_id = self.request.query_params.get('subject')
        if subject_id:
            try:
                queryset = queryset.filter(subject_id=int(subject_id))
            except ValueError:
                queryset = queryset.none()

        return queryset.order_by('-date', '-id')


@extend_schema_view(
    get=extend_schema(
        tags=['Оценки'],
        summary='Получить оценку',
        description='Возвращает одну оценку по её ID.',
    ),
    put=extend_schema(
        tags=['Оценки'],
        summary='Полностью обновить оценку',
        description='Полностью обновляет оценку. Доступно преподавателю.',
    ),
    patch=extend_schema(
        tags=['Оценки'],
        summary='Частично обновить оценку',
        description='Частично обновляет оценку. Доступно преподавателю.',
    ),
    delete=extend_schema(
        tags=['Оценки'],
        summary='Удалить оценку',
        description='Удаляет оценку. Доступно преподавателю.',
    ),
)
class GradeDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = GradeSerializer
    permission_classes = [IsAuthenticated, IsGradeOwnerOrTeacher]

    def get_queryset(self):
        return Grade.objects.select_related('student', 'subject').all()


@extend_schema(
    tags=['Оценки'],
    summary='Создать оценку',
    description='Создаёт новую оценку для студента. Доступно только преподавателю.',
)
class GradeCreateView(generics.CreateAPIView):
    serializer_class = GradeCreateSerializer
    permission_classes = [IsAuthenticated, IsTeacher]

    def perform_create(self, serializer):
        serializer.save()


@extend_schema(
    tags=['Статистика'],
    summary='Получить средний балл',
    description='Возвращает средний балл текущего авторизованного студента.',
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