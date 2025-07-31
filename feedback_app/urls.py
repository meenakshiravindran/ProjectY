from django.urls import path
from . import views

urlpatterns = [
    path('', views.user_login, name='login'),
    path('index/', views.index, name='index'),
    path('logout/', views.user_logout, name='logout'),
    path('programmes/', views.programme_list, name='programme_list'),
    path('programmes/add/', views.add_programme, name='add_programme'),
    path('programmes/edit/<str:pgm_id>/', views.edit_programme, name='edit_programme'),
    path('programmes/delete/<str:pgm_id>/', views.delete_programme, name='delete_programme'),
    path('courses/', views.course_list, name='course_list'),
    path('courses/add/', views.add_course, name='add_course'),
    path('courses/edit/<int:pk>/', views.edit_course, name='edit_course'),
    path('courses/delete/<int:pk>/', views.delete_course, name='delete_course'),
    path('courses/<int:course_id>/batches/', views.batch_list, name='batch_list'),
    path('courses/<int:course_id>/batches/add/', views.add_batch, name='add_batch'),
    path('batches/edit/<int:batch_id>/', views.edit_batch, name='edit_batch'),
    path('batches/delete/<int:batch_id>/', views.delete_batch, name='delete_batch'),
    path('teachers/', views.teacher_list, name='teacher_list'),
    path('teachers/add/', views.add_teacher, name='add_teacher'),
    path('teachers/edit/<int:teacher_id>/', views.edit_teacher, name='edit_teacher'),
    path('teachers/delete/<int:teacher_id>/', views.delete_teacher, name='delete_teacher'),
    path('teacher/<int:user_id>/change-password/', views.change_teacher_password, name='change_teacher_password'),
    path('teacher/<int:user_id>/reset-password/', views.reset_teacher_password, name='reset_teacher_password'),
    path('assignments/', views.teacher_batch_list, name='teacher_batch_list'),
    path('assignments/add/', views.add_teacher_batch, name='add_teacher_batch'),
    path('assignments/edit/<int:pk>/', views.edit_teacher_batch, name='edit_teacher_batch'),
    path('assignments/delete/<int:pk>/', views.delete_teacher_batch, name='delete_teacher_batch'),
    path('assign-teacher/<int:pk>/', views.assign_teacher_modal, name='assign_teacher_to_batch'),

]
    

