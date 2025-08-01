from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Programme, Department,TeacherBatch
from django.shortcuts import get_object_or_404
from .forms import ProgrammeForm,TeacherBatchAssignForm

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('index')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})
    return render(request, 'login.html')

@login_required
def index(request):
    return render(request, 'index.html')

def user_logout(request):
    logout(request)
    return redirect('login')
@login_required
def programme_list(request):
    programmes = Programme.objects.all()
    return render(request, 'programme_list.html', {'programmes': programmes})

@login_required
def add_programme(request):
    form = ProgrammeForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('programme_list')
    return render(request, 'add_programme.html', {'form': form, 'editing': False})

@login_required
def edit_programme(request, pgm_id):
    programme = get_object_or_404(Programme, pgm_id=pgm_id)
    form = ProgrammeForm(request.POST or None, instance=programme)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('programme_list')
    return render(request, 'add_programme.html', {'form': form, 'editing': True})

@login_required
def delete_programme(request, pgm_id):
    programme = get_object_or_404(Programme, pgm_id=pgm_id)
    if request.method == 'POST':
        programme.delete()
        return redirect('programme_list')
    return render(request, 'delete_programme.html', {'programme': programme})

from .models import Course
from .forms import CourseForm

@login_required
def course_list(request):
    courses = Course.objects.all().prefetch_related('batch_set')
    batch_form = BatchForm()
    return render(request, 'course_list.html', {
        'courses': courses,
        'batch_form': batch_form
    })

@login_required
def add_course(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('course_list')
    else:
        form = CourseForm()
    return render(request, 'add_course.html', {'form': form})

@login_required
def edit_course(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            return redirect('course_list')
    else:
        form = CourseForm(instance=course)
    return render(request, 'add_course.html', {'form': form})

@login_required
def delete_course(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        course.delete()
        return redirect('course_list')
    return render(request, 'delete_course.html', {'course': course})


from django.shortcuts import render, get_object_or_404, redirect
from .models import Batch, Course
from .forms import BatchForm

@login_required
def batch_list(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    batches = Batch.objects.filter(course=course)
    return render(request, 'batch_list.html', {'course': course, 'batches': batches})

@login_required
def add_batch(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    if request.method == 'POST':
        form = BatchForm(request.POST)
        if form.is_valid():
            batch = form.save(commit=False)
            batch.course = course
            batch.save()
            return redirect('course_list')
    else:
        form = BatchForm()
    return render(request, 'add_batch.html', {'form': form, 'course': course})

@login_required
def edit_batch(request, batch_id):
    batch = get_object_or_404(Batch, pk=batch_id)
    if request.method == 'POST':
        form = BatchForm(request.POST, instance=batch)
        if form.is_valid():
            form.save()
            return redirect('batch_list', course_id=batch.course.pk)
    else:
        form = BatchForm(instance=batch)
    return render(request, 'add_batch.html', {'form': form, 'course': batch.course})

@login_required
def delete_batch(request, batch_id):
    batch = get_object_or_404(Batch, pk=batch_id)
    course_id = batch.course.pk
    if request.method == 'POST':
        batch.delete()
        return redirect('batch_list', course_id=course_id)
    return render(request, 'delete_batch.html', {'batch': batch})

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User
from .models import Teacher
from .forms import TeacherForm,TeacherEditForm  # Add TeacherEditForm separately (without password)

@login_required()

def teacher_list(request):
    teachers = Teacher.objects.all()
    return render(request, 'teacher_list.html', {'teachers': teachers})

@login_required()

def add_teacher(request):
    if request.method == 'POST':
        form = TeacherForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Teacher added successfully!")
                return redirect('teacher_list')
            except Exception as e:
                messages.error(request, f"Error saving teacher: {e}")
        else:
            messages.error(request, "Form is invalid.")
    else:
        form = TeacherForm()
    
    return render(request, 'add_teacher.html', {'form': form})

@login_required()

def edit_teacher(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    user = teacher.user

    if request.method == "POST":
        form = TeacherEditForm(request.POST, instance=teacher)  # Only TeacherEditForm (no password)
        if form.is_valid():
            form.save()
            messages.success(request, "Teacher updated successfully!")
            return redirect('teacher_list')
    else:
        form = TeacherEditForm(instance=teacher)

    return render(request, 'add_teacher.html', {'form': form, 'edit_mode': True})

@login_required()

def delete_teacher(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    if request.method == 'POST':
        teacher.user.delete()
        return redirect('teacher_list')
    return render(request, 'delete_teacher.html', {'teacher': teacher})

@login_required()
def change_teacher_password(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if request.method == 'POST':
        form = PasswordChangeForm(user, request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password updated successfully.')
            return redirect('teacher_list')
    else:
        form = PasswordChangeForm(user)
    return render(request, 'change_password.html', {'form': form, 'username': user.username})
from django.contrib.auth.forms import SetPasswordForm

@login_required()
def reset_teacher_password(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if request.method == 'POST':
        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f'Password reset successfully for {user.username}.')
            return redirect('teacher_list')
    else:
        form = SetPasswordForm(user)
    return render(request, 'reset_password.html', {'form': form, 'username': user.username})


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import TeacherBatch
from .forms import TeacherBatchAssignForm
from collections import defaultdict
from django.db.models import Prefetch

from collections import defaultdict
from django.shortcuts import render
from .models import TeacherBatch

@login_required
def teacher_batch_list(request):
    assignments = TeacherBatch.objects.select_related('teacher', 'batch', 'course', 'department').all()

    grouped = defaultdict(list)
    grouped_info = {}

    for a in assignments:
        # Compose keys based on related objects' IDs to avoid ambiguity
        key = (a.batch.batch_id, a.course.course_id, a.department.dept_id)

        # Store the names/info only once per group
        if key not in grouped_info:
            batch_str = f"{a.batch.acad_year} - {a.batch.part}"
            course_str = f"{a.course.code} - {a.course.name}"
            dept_str = a.department.dept_name
            grouped_info[key] = {
                'batch': batch_str,
                'course': course_str,
                'department': dept_str,
                'batch_id': a.batch.batch_id,
                'course_id': a.course.course_id,
                'department_id': a.department.dept_id,
            }

        # Append teacher names to the group
        grouped[key].append(a.teacher.name)

    # Prepare list to send to template
    grouped_list = []
    for key, teachers in grouped.items():
        info = grouped_info[key]
        info['teachers'] = teachers
        grouped_list.append(info)

    return render(request, 'teacher_batch_list.html', {'assignments': grouped_list})



# ✅ View 2: Add Assignment (Multiple Teachers at Once)
@login_required
def assign_teacher_batch(request):
    if request.method == 'POST':
        form = TeacherBatchAssignForm(request.POST)
        if form.is_valid():
            teachers = form.cleaned_data['teachers']
            batch = form.cleaned_data['batch']
            course = form.cleaned_data['course']
            department = form.cleaned_data['department']

            for teacher in teachers:
                TeacherBatch.objects.create(
                    teacher=teacher,
                    batch=batch,
                    course=course,
                    department=department
                )

            return redirect('teacher_batch_list')
    else:
        form = TeacherBatchAssignForm()

    return render(request, 'add_teacher_batch.html', {'form': form})

@login_required
def edit_teacher_batch_group(request, batch_id, course_id, dept_id):
    batch_obj = get_object_or_404(Batch, batch_id=batch_id)
    course_obj = get_object_or_404(Course, course_id=course_id)
    dept_obj = get_object_or_404(Department, dept_id=dept_id)

    assignments = TeacherBatch.objects.filter(
        batch=batch_obj,
        course=course_obj,
        department=dept_obj,
    )

    assigned_teachers = [a.teacher.teacher_id for a in assignments]


    if request.method == 'POST':
        form = TeacherBatchAssignForm(request.POST)
        if form.is_valid():
            assignments.delete()

            teachers = form.cleaned_data['teachers']
            for teacher in teachers:
                TeacherBatch.objects.create(
                    teacher=teacher,
                    batch=batch_obj,
                    course=course_obj,
                    department=dept_obj
                )
            return redirect('teacher_batch_list')
    else:
        form = TeacherBatchAssignForm(initial={
            'batch': batch_obj,
            'course': course_obj,
            'department': dept_obj,
            'teachers': assigned_teachers
        })

    return render(request, 'add_teacher_batch.html', {'form': form, 'edit_mode': True})


# ✅ View 4: Delete an Assignment
@login_required
def delete_teacher_batch_group(request, batch_id, course_id, dept_id):
    if request.method == 'POST':
        TeacherBatch.objects.filter(
            batch__batch_id=batch_id,
            course__course_id=course_id,
            department__dept_id=dept_id,
        ).delete()
        messages.success(request, "All assignments deleted successfully.")
    return redirect('teacher_batch_list')


