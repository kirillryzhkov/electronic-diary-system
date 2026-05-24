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

urlpatterns = [
    path('subjects/', SubjectListCreateView.as_view(), name='subject-list-create'),
    path('subjects/stats/', SubjectStatisticsView.as_view(), name='subject-stats'),

    path('grades/', GradeListView.as_view(), name='grade-list'),
    path('grades/create/', GradeCreateView.as_view(), name='grade-create'),
    path('grades/<int:pk>/', GradeDetailView.as_view(), name='grade-detail'),

    path('average/', StudentAverageView.as_view(), name='student-average'),

    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
