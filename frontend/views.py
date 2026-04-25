from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView
from django.db.models import Avg, Count
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DeleteView
from django.core.exceptions import PermissionDenied

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