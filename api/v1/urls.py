# api/v1/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    SubjectListCreateView,
    SubjectStatisticsView,
    GradeListView,
    GradeCreateView,
    StudentAverageView,
    GradeDetailView,
)

from .journal import JournalAssignmentsView, JournalCellView, JournalGradeHistoryView, JournalGridView

urlpatterns = [
    path('journal/assignments/', JournalAssignmentsView.as_view(), name='journal-assignments'),
    path('journal/', JournalGridView.as_view(), name='journal-grid'),
    path('journal/cell/', JournalCellView.as_view(), name='journal-cell'),
    path(
        'journal/grades/<int:grade_id>/history/',
        JournalGradeHistoryView.as_view(),
        name='journal-grade-history',
    ),
    path('subjects/', SubjectListCreateView.as_view(), name='subject-list-create'),
    path('subjects/stats/', SubjectStatisticsView.as_view(), name='subject-stats'),

    path('grades/', GradeListView.as_view(), name='grade-list'),
    path('grades/create/', GradeCreateView.as_view(), name='grade-create'),
    path('grades/<int:pk>/', GradeDetailView.as_view(), name='grade-detail'),

    path('average/', StudentAverageView.as_view(), name='student-average'),

    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
