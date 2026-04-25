from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import (
    HomeView,
    CustomLoginView,
    DashboardView,
    GradesView,
    SubjectsView,
    StatsView,
    GradeCreateFrontendView,
    GradeUpdateFrontendView,
    GradeDeleteFrontendView,
    StudyGroupListView,
    StudyGroupCreateView,
    StudyGroupUpdateView,
    StudyGroupDeleteView,
    ClassroomListView,
    ClassroomCreateView,
    ClassroomUpdateView,
    ClassroomDeleteView,
    TeachingAssignmentListView,
    TeachingAssignmentCreateView,
    TeachingAssignmentUpdateView,
    TeachingAssignmentDeleteView,
)

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('grades/', GradesView.as_view(), name='frontend-grades'),
    path('subjects/', SubjectsView.as_view(), name='frontend-subjects'),
    path('stats/', StatsView.as_view(), name='frontend-stats'),
    path('grades/create/', GradeCreateFrontendView.as_view(), name='frontend-grade-create'),
    path('grades/<int:pk>/edit/', GradeUpdateFrontendView.as_view(), name='frontend-grade-edit'),
    path('grades/<int:pk>/delete/', GradeDeleteFrontendView.as_view(), name='frontend-grade-delete'),


    path('groups/', StudyGroupListView.as_view(), name='frontend-groups'),
    path('groups/create/', StudyGroupCreateView.as_view(), name='frontend-group-create'),
    path('groups/<int:pk>/edit/', StudyGroupUpdateView.as_view(), name='frontend-group-edit'),
    path('groups/<int:pk>/delete/', StudyGroupDeleteView.as_view(), name='frontend-group-delete'),

    path('classrooms/', ClassroomListView.as_view(), name='frontend-classrooms'),
    path('classrooms/create/', ClassroomCreateView.as_view(), name='frontend-classroom-create'),
    path('classrooms/<int:pk>/edit/', ClassroomUpdateView.as_view(), name='frontend-classroom-edit'),
    path('classrooms/<int:pk>/delete/', ClassroomDeleteView.as_view(), name='frontend-classroom-delete'),

    path('assignments/', TeachingAssignmentListView.as_view(), name='frontend-assignments'),
    path('assignments/create/', TeachingAssignmentCreateView.as_view(), name='frontend-assignment-create'),
    path('assignments/<int:pk>/edit/', TeachingAssignmentUpdateView.as_view(), name='frontend-assignment-edit'),
    path('assignments/<int:pk>/delete/', TeachingAssignmentDeleteView.as_view(), name='frontend-assignment-delete'),
]