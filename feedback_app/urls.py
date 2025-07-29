# urls.py
from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('manage-teachers/', views.manage_teachers, name='manage_teachers'),
    path('add-teacher/', views.add_teacher, name='add_teacher'),
    path('manage-courses/', views.manage_courses, name='manage_courses'),
    path('add-course/', views.add_course, name='add_course'),
    path('assign-batches/', views.assign_batches, name='assign_batches'),
    path('assign-batch-to-teacher/', views.assign_batch_to_teacher, name='assign_batch_to_teacher'),
    path('feedback/', views.feedback_form, name='feedback_form'),
    path('submit-feedback/', views.submit_feedback, name='submit_feedback'),
    path('teacher-report/', views.teacher_report, name='teacher_report'),
]