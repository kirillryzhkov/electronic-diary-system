from django import forms

from users.models import User
from subjects.models import Subject
from grades.models import Grade
from academic.models import StudyGroup, Classroom, TeachingAssignment, Schedule, Attendance, Homework

class UserFullNameChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.full_name

class GradeForm(forms.ModelForm):
    class Meta:
        model = Grade
        fields = [
            'student',
            'subject',
            'value',
            'comment',
            'grade_type',
            'month',
            'semester',
        ]

        labels = {
            'student': 'Студент',
            'subject': 'Предмет',
            'value': 'Оценка',
            'comment': 'Комментарий',
            'grade_type': 'Тип оценки',
            'month': 'Месяц аттестации',
            'semester': 'Полугодие',
        }

        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'value': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 5,
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
            }),
            'grade_type': forms.Select(attrs={'class': 'form-control'}),
            'month': forms.Select(
                choices=[('', '---------')] + [(i, i) for i in range(1, 13)],
                attrs={'class': 'form-control'}
            ),
            'semester': forms.Select(
                choices=[('', '---------'), (1, '1'), (2, '2')],
                attrs={'class': 'form-control'}
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

        self.fields['student'].queryset = User.objects.filter(
            role='student'
        ).order_by('group__name', 'last_name', 'first_name', 'username')
        self.fields['student'].label_from_instance = lambda obj: obj.full_name

        self.fields['subject'].queryset = Subject.objects.order_by('name')

        if user and user.role == 'teacher':
            assignments = TeachingAssignment.objects.filter(
                teacher=user
            ).select_related('subject', 'group')

            group_ids = assignments.values_list('group_id', flat=True).distinct()
            subject_ids = assignments.values_list('subject_id', flat=True).distinct()

            self.fields['student'].queryset = User.objects.filter(
                role='student',
                group_id__in=group_ids
            ).order_by('group__name', 'last_name', 'first_name', 'username')

            self.fields['subject'].queryset = Subject.objects.filter(
                id__in=subject_ids
            ).order_by('name')

    def clean(self):
        cleaned_data = super().clean()

        student = cleaned_data.get('student')
        subject = cleaned_data.get('subject')
        value = cleaned_data.get('value')
        grade_type = cleaned_data.get('grade_type')
        month = cleaned_data.get('month')
        semester = cleaned_data.get('semester')

        if value is not None and (value < 1 or value > 5):
            raise forms.ValidationError('Оценка должна быть от 1 до 5.')

        if grade_type == 'monthly' and not month:
            raise forms.ValidationError('Для месячной аттестации нужно указать месяц.')

        if grade_type in ['semester', 'exam'] and not semester:
            raise forms.ValidationError('Для сессии и экзамена нужно указать полугодие.')

        if self.user and self.user.role == 'teacher' and student and subject:
            has_assignment = TeachingAssignment.objects.filter(
                teacher=self.user,
                group=student.group,
                subject=subject
            ).exists()

            if not has_assignment:
                raise forms.ValidationError(
                    'Вы можете выставлять оценку только по своим предметам и своим группам.'
                )

        return cleaned_data


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'description']

        labels = {
            'name': 'Название предмета',
            'description': 'Описание предмета',
        }

        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: Математика'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Краткое описание предмета'
            }),
        }


class StudyGroupForm(forms.ModelForm):
    class Meta:
        model = StudyGroup
        fields = ['name', 'curator', 'description']

        labels = {
            'name': 'Название группы',
            'curator': 'Куратор',
            'description': 'Описание',
        }

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'curator': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['curator'].queryset = User.objects.filter(
            role='teacher'
        ).order_by('last_name', 'first_name', 'username')

        self.fields['curator'].label_from_instance = lambda obj: obj.full_name


class ClassroomForm(forms.ModelForm):
    class Meta:
        model = Classroom
        fields = ['number', 'description']

        labels = {
            'number': 'Номер кабинета',
            'description': 'Описание',
        }

        widgets = {
            'number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: 204'
            }),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: Кабинет математики'
            }),
        }


class TeachingAssignmentForm(forms.ModelForm):
    class Meta:
        model = TeachingAssignment
        fields = ['teacher', 'subject', 'group', 'classroom']

        labels = {
            'teacher': 'Преподаватель',
            'subject': 'Предмет',
            'group': 'Группа',
            'classroom': 'Кабинет',
        }

        widgets = {
            'teacher': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'group': forms.Select(attrs={'class': 'form-control'}),
            'classroom': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['teacher'].queryset = User.objects.filter(
            role='teacher'
        ).order_by('last_name', 'first_name', 'username')

        self.fields['teacher'].label_from_instance = lambda obj: obj.full_name

        self.fields['subject'].queryset = Subject.objects.all().order_by('name')
        self.fields['group'].queryset = StudyGroup.objects.all().order_by('name')
        self.fields['classroom'].queryset = Classroom.objects.all().order_by('number')


class ScheduleForm(forms.ModelForm):
    class Meta:
        model = Schedule
        fields = ['assignment', 'day', 'lesson_number', 'start_time', 'end_time']

        labels = {
            'assignment': 'Назначение',
            'day': 'День недели',
            'lesson_number': 'Номер пары/урока',
            'start_time': 'Время начала',
            'end_time': 'Время окончания',
        }

        widgets = {
            'assignment': forms.Select(attrs={'class': 'form-control'}),
            'day': forms.Select(attrs={'class': 'form-control'}),
            'lesson_number': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'placeholder': 'Например: 1'
            }),
            'start_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'end_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['assignment'].queryset = TeachingAssignment.objects.select_related(
            'teacher',
            'subject',
            'group',
            'classroom'
        ).order_by(
            'group__name',
            'subject__name',
            'teacher__last_name',
            'teacher__first_name'
        )

        self.fields['assignment'].label_from_instance = self.assignment_label

    def assignment_label(self, obj):
        classroom = obj.classroom.number if obj.classroom else 'без кабинета'
        return f'{obj.teacher.full_name} — {obj.subject.name} — {obj.group.name} — каб. {classroom}'

    def clean(self):
        cleaned_data = super().clean()

        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if start_time and end_time and end_time <= start_time:
            raise forms.ValidationError(
                'Время окончания должно быть позже времени начала.'
            )

        return cleaned_data
    
class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['student', 'assignment', 'date', 'status', 'comment']

        labels = {
            'student': 'Студент',
            'assignment': 'Назначение',
            'date': 'Дата',
            'status': 'Статус',
            'comment': 'Комментарий',
        }

        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'assignment': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Например: отсутствовал по уважительной причине'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        self.fields['student'].queryset = User.objects.filter(
            role='student'
        ).order_by('group__name', 'last_name', 'first_name', 'username')

        self.fields['student'].label_from_instance = lambda obj: obj.full_name

        self.fields['assignment'].queryset = TeachingAssignment.objects.select_related(
            'teacher',
            'subject',
            'group',
            'classroom'
        ).order_by('group__name', 'subject__name')

        self.fields['assignment'].label_from_instance = self.assignment_label

        if self.user and self.user.role == 'teacher':
            assignments = TeachingAssignment.objects.filter(
                teacher=self.user
            ).select_related('subject', 'group', 'classroom')

            group_ids = assignments.values_list('group_id', flat=True).distinct()

            self.fields['assignment'].queryset = assignments
            self.fields['student'].queryset = User.objects.filter(
                role='student',
                group_id__in=group_ids
            ).order_by('group__name', 'last_name', 'first_name', 'username')

    def assignment_label(self, obj):
        classroom = obj.classroom.number if obj.classroom else 'без кабинета'
        return f'{obj.teacher.full_name} — {obj.subject.name} — {obj.group.name} — каб. {classroom}'

    def clean(self):
        cleaned_data = super().clean()

        student = cleaned_data.get('student')
        assignment = cleaned_data.get('assignment')

        if student and assignment:
            if student.group != assignment.group:
                raise forms.ValidationError(
                    'Студент должен принадлежать группе выбранного назначения.'
                )

            if self.user and self.user.role == 'teacher':
                if assignment.teacher != self.user:
                    raise forms.ValidationError(
                        'Вы можете отмечать посещаемость только по своим назначениям.'
                    )

        return cleaned_data
    

class HomeworkForm(forms.ModelForm):
    class Meta:
        model = Homework
        fields = ['assignment', 'title', 'description', 'deadline']

        labels = {
            'assignment': 'Назначение',
            'title': 'Тема задания',
            'description': 'Описание задания',
            'deadline': 'Срок сдачи',
        }

        widgets = {
            'assignment': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: Решить задачи по теме'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Подробно опишите домашнее задание'
            }),
            'deadline': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        queryset = TeachingAssignment.objects.select_related(
            'teacher',
            'subject',
            'group',
            'classroom'
        ).order_by(
            'group__name',
            'subject__name',
            'teacher__last_name',
            'teacher__first_name'
        )

        if self.user and self.user.role == 'teacher':
            queryset = queryset.filter(teacher=self.user)

        self.fields['assignment'].queryset = queryset
        self.fields['assignment'].label_from_instance = self.assignment_label

    def assignment_label(self, obj):
        classroom = obj.classroom.number if obj.classroom else 'без кабинета'
        return f'{obj.teacher.full_name} — {obj.subject.name} — {obj.group.name} — каб. {classroom}'

    def clean(self):
        cleaned_data = super().clean()

        assignment = cleaned_data.get('assignment')

        if self.user and self.user.role == 'teacher' and assignment:
            if assignment.teacher != self.user:
                raise forms.ValidationError(
                    'Вы можете создавать домашние задания только по своим назначениям.'
                )

        return cleaned_data
    

class BulkGradeAssignmentForm(forms.Form):
    assignment = forms.ModelChoiceField(
        queryset=TeachingAssignment.objects.none(),
        label='Группа и предмет',
        empty_label='Выберите группу и предмет'
    )

    grade_type = forms.ChoiceField(
        choices=Grade.GRADE_TYPE_CHOICES,
        label='Тип оценки',
        initial='current'
    )

    month = forms.ChoiceField(
        choices=[('', '---------')] + [(i, i) for i in range(1, 13)],
        required=False,
        label='Месяц аттестации'
    )

    semester = forms.ChoiceField(
        choices=[('', '---------'), (1, '1'), (2, '2')],
        required=False,
        label='Полугодие'
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        queryset = TeachingAssignment.objects.select_related(
            'teacher',
            'subject',
            'group',
            'classroom'
        ).filter(
            teacher=user
        ).order_by(
            'group__name',
            'subject__name'
        )

        self.fields['assignment'].queryset = queryset
        self.fields['assignment'].label_from_instance = self.assignment_label

    def assignment_label(self, obj):
        classroom = obj.classroom.number if obj.classroom else 'без кабинета'
        return f'{obj.group.name} — {obj.subject.name} — каб. {classroom}'

    def clean(self):
        cleaned_data = super().clean()

        grade_type = cleaned_data.get('grade_type')
        month = cleaned_data.get('month')
        semester = cleaned_data.get('semester')

        if grade_type == 'monthly' and not month:
            raise forms.ValidationError(
                'Для месячной аттестации нужно указать месяц.'
            )

        if grade_type in ['semester', 'exam'] and not semester:
            raise forms.ValidationError(
                'Для полугодовой сессии и экзамена нужно указать полугодие.'
            )

        return cleaned_data
    

class GroupSummaryReportForm(forms.Form):
    assignment = forms.ModelChoiceField(
        queryset=TeachingAssignment.objects.none(),
        label='Группа и предмет',
        empty_label='Выберите группу и предмет'
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        queryset = TeachingAssignment.objects.select_related(
            'teacher',
            'subject',
            'group',
            'classroom'
        )

        if user and user.role == 'teacher':
            queryset = queryset.filter(teacher=user)

        queryset = queryset.order_by(
            'group__name',
            'subject__name',
            'teacher__last_name',
            'teacher__first_name'
        )

        self.fields['assignment'].queryset = queryset
        self.fields['assignment'].label_from_instance = self.assignment_label

    def assignment_label(self, obj):
        classroom = obj.classroom.number if obj.classroom else 'без кабинета'
        teacher_name = obj.teacher.full_name if obj.teacher else '—'
        return f'{obj.group.name} — {obj.subject.name} — {teacher_name} — каб. {classroom}'