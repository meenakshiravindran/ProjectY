from django import forms
from .models import Programme,Course,Batch,Teacher
from django.contrib.auth.models import User

LEVEL_CHOICES = [
    ('UG', 'UG'),
    ('PG', 'PG'),
    ('IPG', 'IPG'),
    ('FYUG', 'FYUG'),
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
            'level': forms.Select(choices=LEVEL_CHOICES),
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
        
class BatchForm(forms.ModelForm):
    class Meta:
        model = Batch
        fields = ['acad_year', 'part']


from django import forms
from django.contrib.auth.models import User
from .models import Teacher

class TeacherForm(forms.ModelForm):
    username = forms.CharField(max_length=150, help_text='Required.')
    password = forms.CharField(widget=forms.PasswordInput, help_text='Required.')

    class Meta:
        model = Teacher
        fields = ['username', 'password', 'name', 'dept', 'designation', 'gender', 'role', 'fb_active']
        labels = {
            'name': 'Teacher Name',
            'dept': 'Department',
            'designation': 'Designation',
            'gender': 'Gender',
            'role': 'Role',
            'fb_active': 'Feedback Active?',
        }

    def save(self, commit=True):
        # Save user first
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
