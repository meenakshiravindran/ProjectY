from django import forms
from .models import Programme,Course,Batch

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