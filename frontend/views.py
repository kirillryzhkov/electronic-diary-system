from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView
from django.db.models import Avg, Count
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DeleteView
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from users.models import User

from .forms import GradeForm

from grades.models import Grade
from subjects.models import Subject

from academic.models import StudyGroup, Classroom, TeachingAssignment
from .forms import (
    GradeForm,
    SubjectForm,
    StudyGroupForm,
    ClassroomForm,
    TeachingAssignmentForm,
)




class AdminRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if request.user.role != 'admin':
            raise PermissionDenied('Доступ разрешён только администратору.')
        return super().dispatch(request, *args, **kwargs)


class HomeView(TemplateView):
    template_name = 'frontend/home.html'


class CustomLoginView(LoginView):
    template_name = 'frontend/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return '/dashboard/'


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'frontend/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user

        if user.role == 'admin':
            grades = Grade.objects.select_related('student', 'teacher', 'subject').all()
        elif user.role == 'teacher':
            grades = Grade.objects.select_related('student', 'teacher', 'subject').filter(teacher=user)
        else:
            grades = Grade.objects.select_related('student', 'teacher', 'subject').filter(student=user)

        context['grades_count'] = grades.count()
        context['subjects_count'] = Subject.objects.count()
        context['average'] = round(grades.aggregate(avg=Avg('value'))['avg'] or 0, 2)
        context['recent_grades'] = grades.order_by('-date')[:5]

        return context


class GradesView(LoginRequiredMixin, ListView):
    model = Grade
    template_name = 'frontend/grades.html'
    context_object_name = 'grades'

    def get_queryset(self):
        user = self.request.user

        queryset = Grade.objects.select_related(
            'student',
            'teacher',
            'subject'
        ).order_by('-date')

        if user.role == 'teacher':
            queryset = queryset.filter(teacher=user)

        elif user.role == 'student':
            queryset = queryset.filter(student=user)

        subject_id = self.request.GET.get('subject')
        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['subjects'] = Subject.objects.all()
        return context


class SubjectsView(LoginRequiredMixin, ListView):
    model = Subject
    template_name = 'frontend/subjects.html'
    context_object_name = 'subjects'

    def get_queryset(self):
        return Subject.objects.all()
    
class SubjectCreateFrontendView(LoginRequiredMixin, CreateView):
    model = Subject
    form_class = SubjectForm
    template_name = 'frontend/subject_form.html'
    success_url = reverse_lazy('frontend-subjects')

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != 'admin':
            raise PermissionDenied('Только администратор может создавать предметы.')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, 'Предмет успешно добавлен.')
        return super().form_valid(form)


class SubjectUpdateFrontendView(LoginRequiredMixin, UpdateView):
    model = Subject
    form_class = SubjectForm
    template_name = 'frontend/subject_form.html'
    success_url = reverse_lazy('frontend-subjects')

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != 'admin':
            raise PermissionDenied('Только администратор может редактировать предметы.')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, 'Предмет успешно обновлён.')
        return super().form_valid(form)


class SubjectDeleteFrontendView(LoginRequiredMixin, DeleteView):
    model = Subject
    template_name = 'frontend/subject_confirm_delete.html'
    success_url = reverse_lazy('frontend-subjects')

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != 'admin':
            raise PermissionDenied('Только администратор может удалять предметы.')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, 'Предмет успешно удалён.')
        return super().form_valid(form)


class StatsView(LoginRequiredMixin, TemplateView):
    template_name = 'frontend/stats.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != 'teacher':
            from django.shortcuts import redirect
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        subjects = Subject.objects.annotate(
            total_grades=Count('grades'),
            average=Avg('grades__value')
        )

        context['subjects'] = subjects
        return context
    
class GradeCreateFrontendView(LoginRequiredMixin, CreateView):
    template_name = 'frontend/grade_form.html'
    form_class = GradeForm
    success_url = reverse_lazy('frontend-grades')

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != 'teacher':
            raise PermissionDenied('Только учитель может создавать оценки.')
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.teacher = self.request.user
        messages.success(self.request, 'Оценка успешно добавлена.')
        return super().form_valid(form)
    
class GradeUpdateFrontendView(LoginRequiredMixin, UpdateView):
    model = Grade
    template_name = 'frontend/grade_form.html'
    form_class = GradeForm
    success_url = reverse_lazy('frontend-grades')

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != 'teacher':
            raise PermissionDenied('Только учитель может редактировать оценки.')
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Оценка успешно обновлена.')
        return super().form_valid(form)
    
    def get_queryset(self):
        user = self.request.user

        queryset = Grade.objects.select_related('student', 'teacher', 'subject')

        if user.role == 'teacher':
            queryset = queryset.filter(teacher=user)

        return queryset


class GradeDeleteFrontendView(LoginRequiredMixin, DeleteView):
    model = Grade
    template_name = 'frontend/grade_confirm_delete.html'
    success_url = reverse_lazy('frontend-grades')

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != 'teacher':
            raise PermissionDenied('Только учитель может удалять оценки.')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, 'Оценка успешно удалена.')
        return super().form_valid(form)
    
    def get_queryset(self):
        user = self.request.user

        queryset = Grade.objects.select_related('student', 'teacher', 'subject')

        if user.role == 'teacher':
            queryset = queryset.filter(teacher=user)

        return queryset
    

class StudyGroupListView(LoginRequiredMixin, ListView):
    model = StudyGroup
    template_name = 'frontend/groups.html'
    context_object_name = 'groups'

    def get_queryset(self):
        return StudyGroup.objects.select_related('curator').all()


class StudyGroupCreateView(AdminRequiredMixin, CreateView):
    model = StudyGroup
    form_class = StudyGroupForm
    template_name = 'frontend/group_form.html'
    success_url = reverse_lazy('frontend-groups')

    def form_valid(self, form):
        messages.success(self.request, 'Группа успешно добавлена.')
        return super().form_valid(form)


class StudyGroupUpdateView(AdminRequiredMixin, UpdateView):
    model = StudyGroup
    form_class = StudyGroupForm
    template_name = 'frontend/group_form.html'
    success_url = reverse_lazy('frontend-groups')

    def form_valid(self, form):
        messages.success(self.request, 'Группа успешно обновлена.')
        return super().form_valid(form)


class StudyGroupDeleteView(AdminRequiredMixin, DeleteView):
    model = StudyGroup
    template_name = 'frontend/group_confirm_delete.html'
    success_url = reverse_lazy('frontend-groups')

    def form_valid(self, form):
        messages.success(self.request, 'Группа успешно удалена.')
        return super().form_valid(form)


class ClassroomListView(LoginRequiredMixin, ListView):
    model = Classroom
    template_name = 'frontend/classrooms.html'
    context_object_name = 'classrooms'

    def get_queryset(self):
        return Classroom.objects.all()


class ClassroomCreateView(AdminRequiredMixin, CreateView):
    model = Classroom
    form_class = ClassroomForm
    template_name = 'frontend/classroom_form.html'
    success_url = reverse_lazy('frontend-classrooms')

    def form_valid(self, form):
        messages.success(self.request, 'Кабинет успешно добавлен.')
        return super().form_valid(form)


class ClassroomUpdateView(AdminRequiredMixin, UpdateView):
    model = Classroom
    form_class = ClassroomForm
    template_name = 'frontend/classroom_form.html'
    success_url = reverse_lazy('frontend-classrooms')

    def form_valid(self, form):
        messages.success(self.request, 'Кабинет успешно обновлён.')
        return super().form_valid(form)


class ClassroomDeleteView(AdminRequiredMixin, DeleteView):
    model = Classroom
    template_name = 'frontend/classroom_confirm_delete.html'
    success_url = reverse_lazy('frontend-classrooms')

    def form_valid(self, form):
        messages.success(self.request, 'Кабинет успешно удалён.')
        return super().form_valid(form)


class TeachingAssignmentListView(LoginRequiredMixin, ListView):
    model = TeachingAssignment
    template_name = 'frontend/assignments.html'
    context_object_name = 'assignments'

    def get_queryset(self):
        user = self.request.user

        queryset = TeachingAssignment.objects.select_related(
            'teacher',
            'subject',
            'group',
            'classroom'
        )

        if user.role == 'teacher':
            queryset = queryset.filter(teacher=user)

        if user.role == 'student' and user.group:
            queryset = queryset.filter(group=user.group)

        return queryset


class TeachingAssignmentCreateView(AdminRequiredMixin, CreateView):
    model = TeachingAssignment
    form_class = TeachingAssignmentForm
    template_name = 'frontend/assignment_form.html'
    success_url = reverse_lazy('frontend-assignments')

    def form_valid(self, form):
        messages.success(self.request, 'Назначение преподавателя успешно добавлено.')
        return super().form_valid(form)


class TeachingAssignmentUpdateView(AdminRequiredMixin, UpdateView):
    model = TeachingAssignment
    form_class = TeachingAssignmentForm
    template_name = 'frontend/assignment_form.html'
    success_url = reverse_lazy('frontend-assignments')

    def form_valid(self, form):
        messages.success(self.request, 'Назначение преподавателя успешно обновлено.')
        return super().form_valid(form)


class TeachingAssignmentDeleteView(AdminRequiredMixin, DeleteView):
    model = TeachingAssignment
    template_name = 'frontend/assignment_confirm_delete.html'
    success_url = reverse_lazy('frontend-assignments')

    def form_valid(self, form):
        messages.success(self.request, 'Назначение преподавателя успешно удалено.')
        return super().form_valid(form)
    
class TeacherGroupsView(LoginRequiredMixin, TemplateView):
    template_name = 'frontend/teacher_groups.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != 'teacher':
            raise PermissionDenied('Эта страница доступна только преподавателю.')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        teacher = self.request.user

        groups = StudyGroup.objects.filter(
            teaching_assignments__teacher=teacher
        ).distinct().order_by('name')

        groups_data = []

        for group in groups:
            assignments = TeachingAssignment.objects.select_related(
                'subject',
                'classroom'
            ).filter(
                teacher=teacher,
                group=group
            )

            students = User.objects.filter(
                role='student',
                group=group
            ).order_by('username')

            grades = Grade.objects.filter(
                teacher=teacher,
                student__group=group
            )

            groups_data.append({
                'group': group,
                'assignments': assignments,
                'students_count': students.count(),
                'grades_count': grades.count(),
                'average': round(grades.aggregate(avg=Avg('value'))['avg'] or 0, 2),
            })

        context['groups_data'] = groups_data
        return context


class TeacherGroupDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'frontend/teacher_group_detail.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != 'teacher':
            raise PermissionDenied('Эта страница доступна только преподавателю.')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        teacher = self.request.user
        group = get_object_or_404(StudyGroup, id=self.kwargs['group_id'])

        has_access = TeachingAssignment.objects.filter(
            teacher=teacher,
            group=group
        ).exists()

        if not has_access:
            raise PermissionDenied('Вы не ведёте эту группу.')

        assignments = TeachingAssignment.objects.select_related(
            'subject',
            'classroom'
        ).filter(
            teacher=teacher,
            group=group
        )

        students = User.objects.filter(
            role='student',
            group=group
        ).order_by('username')

        grades = Grade.objects.select_related(
            'student',
            'teacher',
            'subject'
        ).filter(
            teacher=teacher,
            student__group=group
        ).order_by('-date')

        context['group'] = group
        context['assignments'] = assignments
        context['students'] = students
        context['grades'] = grades
        context['grades_count'] = grades.count()
        context['students_count'] = students.count()
        context['average'] = round(grades.aggregate(avg=Avg('value'))['avg'] or 0, 2)

        return context
    
class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'frontend/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user

        context['profile_user'] = user

        if user.role == 'student':
            grades = Grade.objects.select_related(
                'student',
                'teacher',
                'subject'
            ).filter(student=user).order_by('-date')

            context['grades_count'] = grades.count()
            context['average'] = round(grades.aggregate(avg=Avg('value'))['avg'] or 0, 2)
            context['recent_grades'] = grades[:5]

        elif user.role == 'teacher':
            grades = Grade.objects.select_related(
                'student',
                'teacher',
                'subject'
            ).filter(teacher=user).order_by('-date')

            assignments = TeachingAssignment.objects.select_related(
                'subject',
                'group',
                'classroom'
            ).filter(teacher=user)

            groups = StudyGroup.objects.filter(
                teaching_assignments__teacher=user
            ).distinct()

            context['grades_count'] = grades.count()
            context['average'] = round(grades.aggregate(avg=Avg('value'))['avg'] or 0, 2)
            context['recent_grades'] = grades[:5]
            context['assignments'] = assignments
            context['groups_count'] = groups.count()

        elif user.role == 'admin':
            context['users_count'] = User.objects.count()
            context['students_count'] = User.objects.filter(role='student').count()
            context['teachers_count'] = User.objects.filter(role='teacher').count()
            context['subjects_count'] = Subject.objects.count()
            context['groups_count'] = StudyGroup.objects.count()
            context['classrooms_count'] = Classroom.objects.count()
            context['assignments_count'] = TeachingAssignment.objects.count()
            context['grades_count'] = Grade.objects.count()

        return context