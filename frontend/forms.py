from django import forms

from users.models import User
from subjects.models import Subject
from grades.models import Grade
from academic.models import StudyGroup, Classroom, TeachingAssignment


class GradeForm(forms.ModelForm):
    class Meta:
        model = Grade
        fields = ['student', 'subject', 'value', 'comment']

        labels = {
            'student': 'Ученик',
            'subject': 'Предмет',
            'value': 'Оценка',
            'comment': 'Пояснение к оценке',
        }

        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'value': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 5,
                'placeholder': 'Введите оценку от 1 до 5'
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Например: хорошо выполнил контрольную работу'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        self.fields['student'].queryset = User.objects.filter(
            role='student'
        ).order_by('username')

        self.fields['subject'].queryset = Subject.objects.all().order_by('name')

        if self.user and self.user.role == 'teacher':
            assignments = self.user.teaching_assignments.select_related(
                'subject',
                'group'
            )

            group_ids = assignments.values_list('group_id', flat=True).distinct()
            subject_ids = assignments.values_list('subject_id', flat=True).distinct()

            self.fields['student'].queryset = User.objects.filter(
                role='student',
                group_id__in=group_ids
            ).order_by('group__name', 'username')

            self.fields['subject'].queryset = Subject.objects.filter(
                id__in=subject_ids
            ).order_by('name')

    def clean_value(self):
        value = self.cleaned_data.get('value')

        if value < 1 or value > 5:
            raise forms.ValidationError('Оценка должна быть от 1 до 5.')

        return value

    def clean(self):
        cleaned_data = super().clean()

        student = cleaned_data.get('student')
        subject = cleaned_data.get('subject')

        if self.user and self.user.role == 'teacher' and student and subject:
            has_assignment = self.user.teaching_assignments.filter(
                group=student.group,
                subject=subject
            ).exists()

            if not has_assignment:
                raise forms.ValidationError(
                    'Вы не можете поставить оценку этому ученику по выбранному предмету.'
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
        ).order_by('username')


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
        ).order_by('username')

        self.fields['subject'].queryset = Subject.objects.all().order_by('name')
        self.fields['group'].queryset = StudyGroup.objects.all().order_by('name')
        self.fields['classroom'].queryset = Classroom.objects.all().order_by('number')