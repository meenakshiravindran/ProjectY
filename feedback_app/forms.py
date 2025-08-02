from django import forms
from .models import Programme,Course,Batch,TeacherBatch, Teacher
from django.contrib.auth.models import User

LEVEL_CHOICES = [
    ('UG', 'UG'),
    ('PG', 'PG'),
    ('IPG', 'IPG'),
    ('FYUG', 'FYUG'),
]
GENDER_CHOICES = [
    ('Male', 'Male'),
    ('Female', 'Female'),
    ('Other', 'Other'),
]

DESIGNATION_CHOICES = [
    ('Assistant Professor', 'Assistant Professor'),
    ('Associate Professor', 'Associate Professor'),
    ('Professor', 'Professor'),
    ('Guest Lecturer', 'Guest Lecturer'),
]

class ProgrammeForm(forms.ModelForm):
    class Meta:
        model = Programme
        fields = ['pgm_name', 'dept', 'level']
        labels = {
            'pgm_name': 'Programme Name',
            'dept': 'Department',
            'level': 'Level',
        }
        widgets = {
            'pgm_name': forms.TextInput(attrs={'class': 'form-control'}),
            'dept': forms.Select(attrs={'class': 'form-select'}),
            'level': forms.Select(choices=LEVEL_CHOICES, attrs={'class': 'form-select'}),
        }

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['name', 'code', 'credit', 'dept', 'pgm']
        labels = {
            'name': 'Course Name',
            'code': 'Course Code',
            'credit': 'Credit',
            'dept': 'Department',
            'pgm': 'Programme',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'credit': forms.NumberInput(attrs={'class': 'form-control'}),
            'dept': forms.Select(attrs={'class': 'form-select'}),
            'pgm': forms.Select(attrs={'class': 'form-select'}),
        }
class BatchForm(forms.ModelForm):
    class Meta:
        model = Batch
        fields = ['acad_year', 'part']
        labels = {
            'acad_year': 'Academic Year',
            'part': 'Part',
        }
        widgets = {
            'acad_year': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 2023'}),
            'part': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. A or B'}),
        }

from django import forms
from django.contrib.auth.models import User
from .models import Teacher

class TeacherForm(forms.ModelForm):
    username = forms.CharField(
        max_length=150,
        help_text='Required.',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'}),
        help_text='Required.'
    )

    class Meta:
        model = Teacher
        fields = ['name', 'dept', 'designation', 'gender', 'role', 'fb_active']  # ✅ Only model fields here
        labels = {
            'name': 'Teacher Name',
            'dept': 'Department',
            'designation': 'Designation',
            'gender': 'Gender',
            'role': 'Role',
            'fb_active': 'Feedback Active?',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'dept': forms.Select(attrs={'class': 'form-select'}),
            'designation': forms.Select(choices=DESIGNATION_CHOICES, attrs={'class': 'form-select'}),
            'gender': forms.RadioSelect(choices=GENDER_CHOICES),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'fb_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def save(self, commit=True):
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password']
        )
        teacher = super().save(commit=False)
        teacher.user = user
        if commit:
            teacher.save()
        return teacher

class TeacherEditForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = ['name', 'dept', 'designation', 'gender', 'role', 'fb_active']
        labels = {
            'name': 'Teacher Name',
            'dept': 'Department',
            'designation': 'Designation',
            'gender': 'Gender',
            'role': 'Role',
            'fb_active': 'Feedback Active?',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'dept': forms.Select(attrs={'class': 'form-select'}),
            'designation': forms.Select(choices=DESIGNATION_CHOICES, attrs={'class': 'form-select'}),
            'gender': forms.RadioSelect(choices=GENDER_CHOICES),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'fb_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }   

from django import forms
from .models import TeacherBatch, Teacher, Batch, Course, Department

class TeacherBatchAssignForm(forms.Form):
    course = forms.ModelChoiceField(
        queryset=Course.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    batch = forms.ModelChoiceField(
        queryset=Batch.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    teachers = forms.ModelMultipleChoiceField(
        queryset=Teacher.objects.all(),
        widget=forms.CheckboxSelectMultiple()
    )

from django import forms
from .models import FeedbackQuestion, FeedbackQOption

class FeedbackQuestionForm(forms.ModelForm):
    class Meta:
        model = FeedbackQuestion
        fields = ['q_id', 'q_desc', 'q_type', 'active']
        widgets = {
            'q_type': forms.Select(choices=[('MCQ', 'MCQ'), ('DESC', 'Descriptive')]),
            'q_desc': forms.Textarea(attrs={'rows': 3}),
        }

    # Remove the options field from here since we're handling it separately
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['q_id'].widget.attrs.update({'class': 'form-control'})
        self.fields['q_desc'].widget.attrs.update({'class': 'form-control'})
        self.fields['q_type'].widget.attrs.update({'class': 'form-control'})

class FeedbackQOptionForm(forms.ModelForm):
    class Meta:
        model = FeedbackQOption
        fields = ['q', 'ans_id', 'answer']
        widgets = {
            'q': forms.HiddenInput(),
            'ans_id': forms.TextInput(attrs={'class': 'form-control'}),
            'answer': forms.TextInput(attrs={'class': 'form-control'}),
        }
