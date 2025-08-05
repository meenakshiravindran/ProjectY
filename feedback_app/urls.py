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

    path('batch/edit/<int:batch_id>/', views.edit_batch, name='edit_batch'),
    path('batch/delete/<int:batch_id>/', views.delete_batch, name='delete_batch'),

    path('teachers/', views.teacher_list, name='teacher_list'),
    path('teachers/add/', views.add_teacher, name='add_teacher'),
    path('teachers/edit/<int:pk>/', views.edit_teacher, name='edit_teacher'),
    path('teachers/delete/<int:pk>/', views.delete_teacher, name='delete_teacher'),
    path('teacher/<int:user_id>/change-password/', views.change_teacher_password, name='change_teacher_password'),
    path('teacher/<int:user_id>/reset-password/', views.reset_teacher_password, name='reset_teacher_password'),
    path('teachers/<int:teacher_id>/toggle_feedback/', views.toggle_feedback_status, name='toggle_feedback'),


    path('teacher-batch/', views.teacher_batch_list, name='teacher_batch_list'),
    path('teacher-batch/add/', views.assign_teacher_batch, name='assign_teacher_batch'),
    path('teacher-batch/edit/<int:batch_id>/<int:course_id>/<int:dept_id>/', views.edit_teacher_batch_group, name='edit_teacher_batch_group'),
    path('teacher-batch/delete/<int:batch_id>/<int:course_id>/<int:dept_id>/', views.delete_teacher_batch_group, name='delete_teacher_batch_group'),
    path('questions/', views.list_questions, name='list_questions'),
    path('questions/add/', views.add_question, name='add_question'),
    path('questions/<str:q_id>/delete/', views.delete_question, name='delete_question'),
    path('questions/<str:q_id>/toggle/', views.toggle_question_status, name='toggle_question_status'),
    
    # Option management URLs
    path('questions/<str:q_id>/options/', views.add_options, name='add_options'),
    path('options/<int:option_id>/delete/', views.delete_option, name='delete_option'),

     path('student-feedback/', views.student_feedback_form, name='student_feedback_form'),
    path('student-feedback/submit/', views.submit_student_feedback, name='submit_student_feedback'),
    
    # Admin Feedback Response URLs (login required)
    path('feedback-admin/student-responses/', views.admin_student_feedback_responses, name='admin_student_feedback_responses'),
    path('student-feedback/teachers/', views.select_teacher_for_feedback, name='select_teacher_for_feedback'),
    path('student-feedback/teacher/<int:teacher_id>/', views.student_feedback_form_by_teacher, name='student_feedback_form_by_teacher'),

    path('ajax/load-courses-teachers/', views.get_courses_teachers_by_department, name='load_courses_teachers'),
    path('ajax/load-batches/', views.load_batches, name='load_batches'),

]

