# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Teacher, Course, Programme, Batch, TeacherBatch, Feedback, Department
import json
from django.contrib.auth.models import User

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    try:
        teacher = Teacher.objects.get(user=request.user)
        context = {
            'teacher': teacher,
            'is_admin': request.user.is_superuser,
            'is_hod': teacher.role == 'HOD'
        }
        return render(request, 'dashboard.html', context)
    except Teacher.DoesNotExist:
        if request.user.is_superuser:
            return render(request, 'admin_dashboard.html')
        return redirect('login')

@login_required
def manage_teachers(request):
    if not request.user.is_superuser:
        return redirect('dashboard')
    
    teachers = Teacher.objects.all()
    departments = Department.objects.all()
    return render(request, 'manage_teachers.html', {
        'teachers': teachers,
        'departments': departments
    })

@login_required
def add_teacher(request):
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        name = data.get('name')
        role = data.get('role')
        department_id = data.get('department')
        
        user = User.objects.create_user(username=username, password=password)
        department = Department.objects.get(id=department_id)
        Teacher.objects.create(
            user=user,
            name=name,
            role=role,
            department=department
        )
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def manage_courses(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    if teacher.role != 'HOD':
        return redirect('dashboard')
    
    programmes = Programme.objects.filter(department=teacher.department)
    courses = Course.objects.filter(department=teacher.department)
    return render(request, 'manage_courses.html', {
        'programmes': programmes,
        'courses': courses
    })

@login_required
def add_course(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    if teacher.role != 'HOD':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    if request.method == 'POST':
        data = json.loads(request.body)
        name = data.get('name')
        code = data.get('code')
        programme_id = data.get('programme')
        
        programme = Programme.objects.get(id=programme_id)
        Course.objects.create(
            name=name,
            code=code,
            programme=programme,
            department=teacher.department
        )
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def assign_batches(request):
    if not request.user.is_superuser:
        return redirect('dashboard')
    
    teachers = Teacher.objects.all()
    batches = Batch.objects.all()
    courses = Course.objects.all()
    teacher_batches = TeacherBatch.objects.all()
    
    return render(request, 'assign_batches.html', {
        'teachers': teachers,
        'batches': batches,
        'courses': courses,
        'teacher_batches': teacher_batches
    })

@login_required
def assign_batch_to_teacher(request):
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    if request.method == 'POST':
        data = json.loads(request.body)
        teacher_id = data.get('teacher')
        batch_id = data.get('batch')
        course_id = data.get('course')
        
        teacher = Teacher.objects.get(id=teacher_id)
        batch = Batch.objects.get(id=batch_id)
        course = Course.objects.get(id=course_id)
        
        TeacherBatch.objects.create(
            teacher=teacher,
            batch=batch,
            course=course
        )
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def feedback_form(request):
    if not request.user.is_superuser:
        return redirect('dashboard')
    
    teachers = Teacher.objects.all()
    batches = Batch.objects.all()
    courses = Course.objects.all()
    
    return render(request, 'feedback_form.html', {
        'teachers': teachers,
        'batches': batches,
        'courses': courses
    })

@login_required
def submit_feedback(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        teacher_id = data.get('teacher')
        batch_id = data.get('batch')
        course_id = data.get('course')
        rating = data.get('rating')
        comments = data.get('comments')
        
        teacher = Teacher.objects.get(id=teacher_id)
        batch = Batch.objects.get(id=batch_id)
        course = Course.objects.get(id=course_id)
        
        Feedback.objects.create(
            teacher=teacher,
            batch=batch,
            course=course,
            rating=rating,
            comments=comments
        )
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def teacher_report(request):
    if not request.user.is_superuser:
        return redirect('dashboard')
    
    teacher_batches = TeacherBatch.objects.select_related('teacher', 'batch', 'course').all()
    
    # Create table data
    table_data = []
    for tb in teacher_batches:
        feedbacks = Feedback.objects.filter(
            teacher=tb.teacher,
            batch=tb.batch,
            course=tb.course
        )
        
        avg_rating = 0
        if feedbacks.exists():
            avg_rating = sum(f.rating for f in feedbacks) / feedbacks.count()
        
        table_data.append({
            'teacher': tb.teacher.name,
            'role': tb.teacher.role,
            'department': tb.teacher.department.name,
            'course': tb.course.name,
            'programme': tb.batch.programme.name,
            'batch': tb.batch.name,
            'teacher_batch': f"{tb.teacher.name} - {tb.batch.name}",
            'avg_rating': round(avg_rating, 1) if avg_rating else 'No feedback'
        })
    
    return render(request, 'teacher_report.html', {'table_data': table_data})
