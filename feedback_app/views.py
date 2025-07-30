from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Programme, Department
from django.shortcuts import get_object_or_404
from .forms import ProgrammeForm

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
    return render(request, 'course_list.html', {'courses': courses})

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
