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

    SubjectCreateFrontendView,
    SubjectUpdateFrontendView,
    SubjectDeleteFrontendView,

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

    TeacherGroupsView,
    TeacherGroupDetailView,

    ProfileView,

    ScheduleListView,
    ScheduleCreateView,
    ScheduleUpdateView,
    ScheduleDeleteView,

    AttendanceListView,
    AttendanceCreateView,
    AttendanceUpdateView,
    AttendanceDeleteView,

    HomeworkListView,
    HomeworkCreateView,
    HomeworkUpdateView,
    HomeworkDeleteView,

    GroupGradeEntryView,

    GradeJournalView,
    GradeExportExcelView,
    GradeSummaryReportView,
    GradeSummaryExcelExportView,

    AttendanceExportExcelView,

    NotificationListView,
    NotificationMarkReadView,
    NotificationMarkAllReadView,
)

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('grades/', GradesView.as_view(), name='frontend-grades'),
    path('subjects/', SubjectsView.as_view(), name='frontend-subjects'),
    path('subjects/create/', SubjectCreateFrontendView.as_view(), name='frontend-subject-create'),
    path('subjects/<int:pk>/edit/', SubjectUpdateFrontendView.as_view(), name='frontend-subject-edit'),
    path('subjects/<int:pk>/delete/', SubjectDeleteFrontendView.as_view(), name='frontend-subject-delete'),
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

    path('my-groups/', TeacherGroupsView.as_view(), name='frontend-teacher-groups'),
    path('my-groups/<int:group_id>/', TeacherGroupDetailView.as_view(), name='frontend-teacher-group-detail'),

    path('schedule/', ScheduleListView.as_view(), name='frontend-schedule'),
    path('schedule/create/', ScheduleCreateView.as_view(), name='frontend-schedule-create'),
    path('schedule/<int:pk>/edit/', ScheduleUpdateView.as_view(), name='frontend-schedule-edit'),
    path('schedule/<int:pk>/delete/', ScheduleDeleteView.as_view(), name='frontend-schedule-delete'),

    path('attendance/', AttendanceListView.as_view(), name='frontend-attendance'),
    path('attendance/create/', AttendanceCreateView.as_view(), name='frontend-attendance-create'),
    path('attendance/<int:pk>/edit/', AttendanceUpdateView.as_view(), name='frontend-attendance-edit'),
    path('attendance/<int:pk>/delete/', AttendanceDeleteView.as_view(), name='frontend-attendance-delete'),

    path('homework/', HomeworkListView.as_view(), name='frontend-homework'),
    path('homework/create/', HomeworkCreateView.as_view(), name='frontend-homework-create'),
    path('homework/<int:pk>/edit/', HomeworkUpdateView.as_view(), name='frontend-homework-edit'),
    path('homework/<int:pk>/delete/', HomeworkDeleteView.as_view(), name='frontend-homework-delete'),

    path('grades/group-entry/', GroupGradeEntryView.as_view(), name='frontend-group-grade-entry'),

    path('grades/journal/', GradeJournalView.as_view(), name='frontend-grade-journal'),
    path('grades/export/excel/', GradeExportExcelView.as_view(), name='frontend-grade-export-excel'),
    path('grades/report/', GradeSummaryReportView.as_view(), name='frontend-grade-summary-report'),
    path('grades/report/excel/', GradeSummaryExcelExportView.as_view(), name='frontend-grade-summary-excel'),

    path('attendance/export/excel/', AttendanceExportExcelView.as_view(), name='frontend-attendance-export-excel'),

    path('notifications/', NotificationListView.as_view(), name='frontend-notifications'),
    path('notifications/<int:pk>/read/', NotificationMarkReadView.as_view(), name='frontend-notification-read'),
    path('notifications/read-all/', NotificationMarkAllReadView.as_view(), name='frontend-notifications-read-all'),
]