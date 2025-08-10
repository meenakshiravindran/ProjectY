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
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import datetime, timedelta
import json
from collections import defaultdict, Counter
import calendar

# Import your models
from .models import (
    StudentFeedbackResponse, Teacher, Course, Department, 
    TeacherBatch, FeedbackQOption, TeacherFeedbackResponse,
    Feedback, Programme, Batch
)

@login_required
def index(request):
    user = request.user
    current_date = timezone.now()
    
    # Base context
    context = {
        "current_date": current_date,
        "is_admin": user.is_staff,
        "is_teacher": hasattr(user, 'teacher') and not user.is_staff,
    }
    
    if user.is_staff:
        # Admin Dashboard Data
        context.update(get_admin_dashboard_data())
    elif hasattr(user, 'teacher'):
        # Teacher Dashboard Data
        context.update(get_teacher_dashboard_data(user.teacher))
    
    return render(request, 'index.html', context)

def get_admin_dashboard_data():
    """Generate comprehensive admin dashboard data"""
    
    # Basic statistics
    total_students_submitted = StudentFeedbackResponse.objects.values('session_id').distinct().count()
    active_teachers = Teacher.objects.filter(fb_active=True).count()
    total_courses = Course.objects.count()
    total_departments = Department.objects.count()
    
    # Gender distribution data
    gender_stats = Teacher.objects.exclude(gender__isnull=True).exclude(gender__exact='').values('gender').annotate(count=Count('gender'))
    
    if gender_stats.exists():
        gender_labels = []
        gender_counts = []
        for stat in gender_stats:
            gender_labels.append(stat['gender'].title() if stat['gender'] else 'Not Specified')
            gender_counts.append(stat['count'])
    else:
        # Default data if no gender data exists
        gender_labels = ['Male', 'Female']
        gender_counts = [0, 0]
    
    # Rating distribution (assuming you have rating options)
    rating_options = ['Excellent', 'Good', 'Average', 'Poor','Very Poor']
    rating_counts = []
    
    for option in rating_options:
        count = StudentFeedbackResponse.objects.filter(
            selected_option__answer__icontains=option
        ).count()
        rating_counts.append(count)
    
    # If all counts are 0, provide sample data for demonstration
    if sum(rating_counts) == 0:
        rating_counts = [0, 0, 0, 0, 0]
    
    # Monthly response trend (last 6 months)
    monthly_labels = []
    monthly_counts = []
    current_date = timezone.now()
    
    for i in range(6):
        date = current_date - timedelta(days=30*i)
        month_name = calendar.month_name[date.month]
        monthly_labels.insert(0, f"{month_name[:3]} {date.year}")
        
        # Count responses for this month
        start_date = date.replace(day=1)
        if i == 0:
            end_date = current_date
        else:
            next_month = start_date.replace(month=start_date.month+1) if start_date.month < 12 else start_date.replace(year=start_date.year+1, month=1)
            end_date = next_month - timedelta(days=1)
        
        count = StudentFeedbackResponse.objects.filter(
            submitted_at__range=[start_date, end_date]
        ).count()
        monthly_counts.insert(0, count)
    
    # Department-wise teacher distribution
    dept_stats = Department.objects.annotate(
        teacher_count=Count('teacher')
    ).order_by('-teacher_count')
    
    department_labels = [dept.dept_name for dept in dept_stats]
    department_counts = [dept.teacher_count for dept in dept_stats]
    
    # Recent activities (last 10 feedback responses)
    recent_activities = TeacherFeedbackResponse.objects.select_related(
        'teacher_batch__teacher',
        'teacher_batch__course',
        'teacher_batch__department'
    ).order_by('-created_date_time')[:10]
    
    return {
        'total_feedback_submissions': total_students_submitted,
        'active_teachers': active_teachers,
        'total_courses': total_courses,
        'total_departments': total_departments,
        'gender_labels': json.dumps(gender_labels),
        'gender_counts': json.dumps(gender_counts),
        'rating_labels': json.dumps(rating_options),
        'rating_counts': json.dumps(rating_counts),
        'monthly_labels': json.dumps(monthly_labels),
        'monthly_counts': json.dumps(monthly_counts),
        'department_labels': json.dumps(department_labels),
        'department_counts': json.dumps(department_counts),
        'recent_activities': recent_activities,
    }
from collections import defaultdict
import json

def get_teacher_dashboard_data(teacher):
    """Generate comprehensive teacher dashboard data for a given teacher."""

    # All TeacherBatch entries for this teacher
    teacher_batches = TeacherBatch.objects.filter(teacher=teacher).select_related(
        'course', 'batch', 'department'
    )

    teacher_courses_count = teacher_batches.count()

    # Total feedback responses for this teacher
    teacher_responses_count = StudentFeedbackResponse.objects.filter(
        teacher_batch__teacher=teacher
    ).count()

    # Calculate average rating
    rating_map = {
        'excellent': 5,
        'good': 4,
        'average': 3,
        'poor': 2,
        'very poor': 1,
    }

    rating_responses = StudentFeedbackResponse.objects.filter(
        teacher_batch__teacher=teacher,
        selected_option__isnull=False
    ).select_related('selected_option')

    total_rating = 0
    rating_count = 0
    feedback_distribution = defaultdict(int)

    for response in rating_responses:
        if not response.selected_option or not response.selected_option.answer:
            continue
        option_text = response.selected_option.answer.lower()
        for key, value in rating_map.items():
            if key in option_text:
                total_rating += value
                rating_count += 1
                feedback_distribution[response.selected_option.answer] += 1
                break

    teacher_avg_rating = total_rating / rating_count if rating_count > 0 else 0
    total_questions_count = FeedbackQuestion.objects.filter(active=True).count() 
    
    # Unique students count
    unique_students = StudentFeedbackResponse.objects.filter(
        teacher_batch__teacher=teacher
    ).values('session_id').distinct().count()

    # Prepare chart data for teacher feedback distribution
    teacher_feedback_labels = list(feedback_distribution.keys())
    teacher_feedback_counts = list(feedback_distribution.values())

    # ✅ UPDATED: Batch-wise performance with student count instead of response count
    batch_performance = {}  # Dictionary to group by batch
    batch_labels = []
    batch_ratings = []  # Changed from batch_ratings to batch_student_counts

    # Group responses by batch
    for batch in teacher_batches:
        batch_key = f"{batch.batch.acad_year} {batch.batch.part}"
        
        if batch_key not in batch_performance:
            batch_performance[batch_key] = {
                'total_rating': 0,
                'rating_count': 0,
                'unique_students': 0
            }
        
        # Get unique students for this specific teacher-batch combination
        unique_students_for_batch = StudentFeedbackResponse.objects.filter(
            teacher_batch=batch
        ).values('session_id').distinct().count()
        
        batch_performance[batch_key]['unique_students'] = unique_students_for_batch
        
        # Still calculate ratings for other purposes
        batch_responses = StudentFeedbackResponse.objects.filter(
            teacher_batch=batch
        ).select_related('selected_option')

        for response in batch_responses:
            if response.selected_option and response.selected_option.answer:
                option_text = response.selected_option.answer.lower()
                for key, value in rating_map.items():
                    if key in option_text:
                        batch_performance[batch_key]['total_rating'] += value
                        batch_performance[batch_key]['rating_count'] += 1
                        break

    # ✅ NEW: Sort batch performance by year and part before converting to lists
    def sort_batch_key(item):
        batch_key = item[0]  # The batch key like "2022 A"
        year, part = batch_key.split()
        return (int(year), part)  # Sort by year first, then by part (A, B, etc.)

    sorted_batch_performance = sorted(batch_performance.items(), key=sort_batch_key)

    # Convert sorted batch performance to lists for chart
    for batch_key, data in sorted_batch_performance:
        batch_labels.append(batch_key)
        avg_rating = data['total_rating'] / data['rating_count'] if data['rating_count'] > 0 else 0
        batch_ratings.append(round(avg_rating, 1))

    # ✅ UPDATED: Course-wise performance for the table with student count
    course_performance = []

    for batch in teacher_batches:
        # Get unique students for this specific teacher-batch combination
        unique_students_for_course = StudentFeedbackResponse.objects.filter(
            teacher_batch=batch
        ).values('session_id').distinct().count()
        
        # Still calculate average rating for display
        course_responses = StudentFeedbackResponse.objects.filter(
            teacher_batch=batch
        ).select_related('selected_option')

        course_total = 0
        course_count = 0
        response_count = 0

        for response in course_responses:
            if response.selected_option and response.selected_option.answer:
                option_text = response.selected_option.answer.lower()
                for key, value in rating_map.items():
                    if key in option_text:
                        course_total += value
                        course_count += 1
                        break

        course_avg = course_total / course_count if course_count > 0 else 0

        course_info = {
            'course': batch.course,
            'batch': batch.batch,
            'department': batch.department,
            'students_reached': unique_students_for_course,  # Changed from response_count
            'avg_rating': course_avg
        }
        course_performance.append(course_info)

    return {
        'teacher_courses_count': teacher_courses_count,
        'total_questions_count': total_questions_count,
        'teacher_responses_count': teacher_responses_count,
        'teacher_avg_rating': teacher_avg_rating,
        'unique_students': unique_students,
        'teacher_feedback_labels': json.dumps(teacher_feedback_labels),
        'teacher_feedback_counts': json.dumps(teacher_feedback_counts),
        # ✅ UPDATED: Batch-wise data now shows student counts in sorted order
        'course_labels': json.dumps(batch_labels),  
        'course_student_counts': json.dumps(batch_ratings),  # Changed from course_ratings
        'teacher_courses': course_performance,  # Updated structure
    }

def get_rating_value(option_text):
    """Convert option text to numeric rating"""
    option_lower = option_text.lower()
    rating_map = {
        'excellent': 5,
        'good': 4,
        'average': 3,
        'poor': 2,
        'very poor': 1,
    }
    
    for key, value in rating_map.items():
        if key in option_lower:
            return value
    return 0  # Default if no match found

# Optional: Function to get color scheme for charts
def get_chart_colors(count):
    """Generate color scheme for charts"""
    colors = [
        '#667eea', '#764ba2', '#4CAF50', '#2196F3', 
        '#FF9800', '#f44336', '#9C27B0', '#607D8B'
    ]
    return colors[:count] if count <= len(colors) else colors * (count // len(colors) + 1)

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
    selected_dept = request.GET.get('department')
    departments = Department.objects.all()

    if selected_dept:
        courses = Course.objects.filter(dept__dept_name=selected_dept).prefetch_related('batch_set')
    else:
        courses = Course.objects.all().prefetch_related('batch_set')

    batch_form = BatchForm()
    edit_forms={}
     
    for course in courses:
        for batch in course.batch_set.all():
            edit_forms[batch.batch_id]=BatchForm(instance=batch)

    return render(request, 'course_list.html', {
        'courses': courses,
        'departments': departments,
        'selected_dept': selected_dept,
        'batch_form': batch_form,
        'edit_forms':edit_forms,
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

    # ✅ Always redirect to course list after update (modal submission)
    return redirect('course_list')


@login_required
def delete_batch(request, batch_id):
    batch = get_object_or_404(Batch, pk=batch_id)
    if request.method == 'POST':
        batch.delete()
    return redirect('course_list')

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User
from .models import Teacher
from .forms import TeacherForm,TeacherEditForm  # Add TeacherEditForm separately (without password)

from django.contrib.auth.models import Group
from django.contrib import messages
@login_required()
def teacher_list(request):
    selected_dept = request.GET.get('department')
    departments = Department.objects.all()

    if selected_dept:
        teachers = Teacher.objects.filter(dept__dept_name=selected_dept)
    else:
        teachers = Teacher.objects.all()

    # ✅ This is essential for showing errors in modal
    reset_errors = request.session.pop('reset_errors', None)
    reset_user_id = request.session.pop('reset_user_id', None)

    return render(request, 'teacher_list.html',{
        'teachers': teachers,
        'departments': departments,
        'selected_dept': selected_dept,
        'reset_errors': reset_errors,
        'reset_user_id': reset_user_id,})

@login_required()
def add_teacher(request):
    if request.method == 'POST':
        form = TeacherForm(request.POST,request.FILES)
        if form.is_valid():
            try:
                # Save the form without committing to access the object
                teacher = form.save(commit=False)
                teacher.save()

                # Get the role name from the related Role model
                role_name = teacher.role.role_name.lower().strip()

                # Get or create the Django Group with the same name
                group, _ = Group.objects.get_or_create(name=role_name)

                # Assign the user to this group if a user is linked
                if teacher.user:
                    teacher.user.groups.add(group)

                messages.success(request, "Teacher added and assigned to group successfully!")
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
        form = TeacherEditForm(request.POST,request.FILES, instance=teacher)  # Only TeacherEditForm (no password)
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

@login_required
def change_teacher_password(request, user_id):
    user = get_object_or_404(User, pk=user_id)

    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if not old_password or not new_password or not confirm_password:
            messages.error(request, "All fields are required.")
        elif not user.check_password(old_password):
            messages.error(request, "Old password is incorrect.")
        elif new_password != confirm_password:
            messages.error(request, "New password and confirm password do not match.")
        else:
            user.set_password(new_password)
            user.save()
            update_session_auth_hash(request, user)
            # messages.success(request, f"Password updated successfully for {user.username}.")
    
    return redirect('teacher_list')

from django.contrib.auth.forms import SetPasswordForm

@login_required
def reset_teacher_password(request, teacher_id):
    try:
        teacher = Teacher.objects.get(pk=teacher_id)
        user = teacher.user
    except Teacher.DoesNotExist:
        messages.error(request, "❌ Teacher not found.")
        return redirect('teacher_list')

    if request.method == 'POST':
        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            # messages.success(request, f"✅ Password reset successfully for {user.username}")
        else:
            # ✅ Store errors and teacher ID in session
            request.session['reset_errors'] = form.errors.get_json_data()
            request.session['reset_user_id'] = str(user.id)
            messages.error(request, "❌ Failed to reset password. Please check the input.")
        return redirect('teacher_list')


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
    selected_dept_id = request.GET.get('department')
    departments = Department.objects.all()

    assignments = TeacherBatch.objects.select_related('teacher', 'batch', 'course', 'department')

    # ✅ Only filter if not "All"
    if selected_dept_id and selected_dept_id != "All":
        assignments = assignments.filter(department__dept_id=selected_dept_id)

    from collections import defaultdict
    grouped = defaultdict(list)
    grouped_info = {}

    for a in assignments:
        key = (a.batch.batch_id, a.course.course_id, a.department.dept_id)

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

        grouped[key].append(a.teacher.name)

    grouped_list = []
    for key, teachers in grouped.items():
        info = grouped_info[key]
        info['teachers'] = teachers
        grouped_list.append(info)

    return render(request, 'teacher_batch_list.html', {
        'assignments': grouped_list,
        'departments': departments,
        'selected_dept_id': selected_dept_id or "All",
    })

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

    # Get current teacher assignments for this batch-course-department
    assignments = TeacherBatch.objects.filter(
        batch=batch_obj,
        course=course_obj,
        department=dept_obj,
    )

    # Pass model instances instead of IDs to preserve display labels
    assigned_teachers = [a.teacher for a in assignments]

    if request.method == 'POST':
        form = TeacherBatchAssignForm(request.POST)
        if form.is_valid():
            # Remove old assignments
            assignments.delete()

            # Add updated teachers
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
        # Pre-fill the form with the existing assignments
        form = TeacherBatchAssignForm(initial={
            'batch': batch_obj,
            'course': course_obj,
            'department': dept_obj,
            'teachers': assigned_teachers
        })

    return render(request, 'add_teacher_batch.html', {
        'form': form,
        'edit_mode': True
    })

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

@login_required
def get_courses_teachers_by_department(request):
    dept_id = request.GET.get('department_id')

    courses = Course.objects.filter(dept_id=dept_id).values('course_id', 'code', 'name')
    teachers = Teacher.objects.filter(dept_id=dept_id).values('teacher_id', 'name')

    return JsonResponse({
        'courses': list(courses),
        'teachers': list(teachers)
    })
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Batch

@login_required
def load_batches(request):
    course_id = request.GET.get('course_id')
    batches = Batch.objects.filter(course_id=course_id).values('batch_id', 'acad_year', 'part')
    return JsonResponse({'batches': list(batches)})

# views.py - Enhanced views with improved add_options and toggle functionality

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import FeedbackQuestionForm, FeedbackQOptionForm
from .models import FeedbackQuestion, FeedbackQOption

def add_question(request):
    if request.method == 'POST':
        form = FeedbackQuestionForm(request.POST)
        
        if form.is_valid():
            # Save the question first
            question = form.save()

            # If it's an MCQ, handle adding options
            if form.cleaned_data['q_type'] == 'MCQ':
                # Get options from the POST data (comma-separated list of options)
                options_text = request.POST.get('options', '')
                if options_text:  # Only proceed if options are provided
                    options = [opt.strip() for opt in options_text.split(',') if opt.strip()]
                    
                    # Save the options for this question with proper ans_id
                    for i, option_text in enumerate(options, 1):
                        FeedbackQOption.objects.create(
                            q=question, 
                            ans_id=f"opt_{i}",  # Generate a proper ans_id
                            answer=option_text
                        )
                    
                    messages.success(request, f'Question "{question.q_desc}" created successfully with {len(options)} options!')
                else:
                    messages.warning(request, 'Question created but no options were added. You can add options later.')
            else:
                messages.success(request, f'Descriptive question "{question.q_desc}" created successfully!')

            # Redirect to the list of questions after saving
            return redirect('list_questions')
        else:
            messages.error(request, 'Please correct the errors below.')

    else:
        form = FeedbackQuestionForm()

    return render(request, 'add_question.html', {'form': form})

# List Questions
def list_questions(request):
    questions = FeedbackQuestion.objects.all().order_by('-active', 'q_id')  # Show active questions first
    return render(request, 'list_questions.html', {'questions': questions})

# Simplified Add Options for MCQ (handles both single and multiple options)
def add_options(request, q_id):
    question = get_object_or_404(FeedbackQuestion, pk=q_id)
    
    if question.q_type != 'MCQ':
        messages.error(request, 'Options can only be added to MCQ questions.')
        return redirect('list_questions')
    
    if request.method == 'POST':
        options_text = request.POST.get('options_text', '')
        if options_text:
            options = [opt.strip() for opt in options_text.split(',') if opt.strip()]
            existing_count = FeedbackQOption.objects.filter(q=question).count()
            
            for i, option_text in enumerate(options, existing_count + 1):
                FeedbackQOption.objects.create(
                    q=question,
                    ans_id=f"opt_{i}",
                    answer=option_text
                )
            
            if len(options) == 1:
                messages.success(request, f'Option "{options[0]}" added successfully!')
            else:
                messages.success(request, f'{len(options)} options added successfully!')
            return redirect('add_options', q_id=q_id)
        else:
            messages.error(request, 'Please enter at least one option.')
    
    # GET request - display the form
    options = FeedbackQOption.objects.filter(q=question).order_by('ans_id')
    
    return render(request, 'add_options.html', {
        'question': question, 
        'options': options
    })

# Delete Question View
def delete_question(request, q_id):
    question = get_object_or_404(FeedbackQuestion, q_id=q_id)
    
    if request.method == 'POST':
        question_desc = question.q_desc
        question.delete()
        messages.success(request, f'Question "{question_desc}" deleted successfully!')
        return redirect('list_questions')

    return render(request, 'confirm_delete.html', {'question': question})

# Toggle Question Active Status
def toggle_question_status(request, q_id):
    question = get_object_or_404(FeedbackQuestion, q_id=q_id)
    
    if request.method == 'POST':
        question.active = not question.active
        question.save()
        
        status = "activated" if question.active else "deactivated"
        messages.success(request, f'Question "{question.q_desc}" has been {status}!')
    
    return redirect('list_questions')

@login_required
def toggle_batch_activation(request, batch_id):
    batch = get_object_or_404(Batch, pk=batch_id)
    if request.method == 'POST':
        batch.is_active = not batch.is_active
        batch.save()
        messages.success(request, f'Batch {batch.acad_year} - {batch.part} has been {"activated" if batch.is_active else "deactivated"}!')
    return redirect('course_list')

# Delete individual option
def delete_option(request, option_id):
    option = get_object_or_404(FeedbackQOption, id=option_id)
    question_id = option.q.q_id
    
    if request.method == 'POST':
        option_text = option.answer
        option.delete()
        messages.success(request, f'Option "{option_text}" deleted successfully!')
    
    return redirect('add_options', q_id=question_id)



# Add these views to your existing views.py

from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import uuid
from .models import FeedbackQuestion, FeedbackQOption, StudentFeedbackResponse, Teacher


def student_feedback_form(request):
    """Display feedback form to students (no login required)"""
    teacher_id = request.GET.get('teacher_id')
    teacher = get_object_or_404(Teacher, teacher_id=teacher_id)

    # Get only active questions
    questions = FeedbackQuestion.objects.filter(active=True).order_by('q_id')

    # Generate a unique session ID for this feedback submission
    if 'student_feedback_session' not in request.session:
        request.session['student_feedback_session'] = str(uuid.uuid4())

    # Separate MCQ and Descriptive questions
    mcq_questions = []
    desc_questions = []

    for question in questions:
        if question.q_type == 'MCQ':
            options = FeedbackQOption.objects.filter(q=question).order_by('ans_id')
            mcq_questions.append({
                'question': question,
                'options': options
            })
        elif question.q_type == 'DESC':
            desc_questions.append(question)

    context = {
        'teacher': teacher,
        'mcq_questions': mcq_questions,
        'desc_questions': desc_questions,
        'session_id': request.session['student_feedback_session'],
        'total_questions': questions.count()
    }
    return render(request, 'feedback_form.html', context)


def submit_student_feedback(request):
    """Handle student feedback submission with teacher-course linking."""
    if request.method == 'POST':
        try:
            session_id = request.session.get('student_feedback_session')
            if not session_id:
                return JsonResponse({'success': False, 'error': 'Session expired. Please refresh the page.'})

            # Prevent duplicate submissions
            existing_responses = StudentFeedbackResponse.objects.filter(session_id=session_id)
            if existing_responses.exists():
                return JsonResponse({'success': False, 'error': 'Feedback already submitted from this session.'})

            # Get teacher_batch_id instead of teacher_id
            teacher_batch_id = request.POST.get('teacher_batch_id')
            teacher_batch = TeacherBatch.objects.filter(pk=teacher_batch_id).first() if teacher_batch_id else None
            
            if not teacher_batch:
                return JsonResponse({'success': False, 'error': 'Invalid teacher-course selection.'})

            # Get all active questions
            questions = FeedbackQuestion.objects.filter(active=True)
            unanswered_questions = []
            responses_to_save = []

            for question in questions:
                if question.q_type == 'MCQ':
                    option_id = request.POST.get(f'question_{question.q_id}')
                    if not option_id:
                        unanswered_questions.append(f"Question {question.q_id}")
                    else:
                        try:
                            option = FeedbackQOption.objects.get(id=option_id, q=question)
                            responses_to_save.append({
                                'question': question,
                                'selected_option': option,
                                'session_id': session_id
                            })
                        except FeedbackQOption.DoesNotExist:
                            unanswered_questions.append(f"Question {question.q_id} (Invalid option)")

                elif question.q_type == 'DESC':
                    response_text = request.POST.get(f'question_{question.q_id}', '').strip()
                    if question.is_required and not response_text:
                        unanswered_questions.append(f"Question {question.q_id}")
                    else:
                        responses_to_save.append({
                            'question': question,
                            'response_text': response_text if response_text else None,
                            'session_id': session_id
                        })

            # If unanswered required questions exist, return error
            if unanswered_questions:
                return JsonResponse({
                    'success': False,
                    'error': f'Please answer all required questions. Missing answers for: {", ".join(unanswered_questions)}'
                })

            # Generate feedback number based on teacher-course
            feedback_count = StudentFeedbackResponse.objects.filter(teacher_batch=teacher_batch).values('session_id').distinct().count()
            feedback_number = feedback_count + 1

            # Save responses with teacher_batch relationship
            for response_data in responses_to_save:
                StudentFeedbackResponse.objects.create(
                    question=response_data['question'],
                    selected_option=response_data.get('selected_option'),
                    response_text=response_data.get('response_text'),
                    session_id=session_id,
                    feedback_number=feedback_number,
# Keep for backward compatibility
                    teacher_batch=teacher_batch  # NEW: Link to specific teacher-course
                )

            # Clear session
            if 'student_feedback_session' in request.session:
                del request.session['student_feedback_session']

            return JsonResponse({
                'success': True,
                'message': f'Thank you! Your feedback for {teacher_batch.course.code} has been submitted successfully. (Feedback #{feedback_number})'
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': f'An error occurred: {str(e)}'})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

from django.contrib import messages
from django.contrib.auth.decorators import login_required
@login_required
def admin_student_feedback_responses(request):
    user = request.user

    # Default role flags
    is_admin = user.is_staff
    is_hod = False
    is_teacher = False
    teacher = None

    # Detect role via Teacher → Role relation
    try:
        teacher = Teacher.objects.get(user=user)
        role_name = teacher.role.role_name.lower()
        is_hod = (role_name == "hod")
        is_teacher = (role_name == "teacher")
    except Teacher.DoesNotExist:
        teacher = None
        role_name = None

    total_questions = FeedbackQuestion.objects.filter(active=True).count()
    all_responses = StudentFeedbackResponse.objects.all()

    # Filters from GET params
    selected_dept_id = request.GET.get('department')
    selected_teacher_id = request.GET.get('teacher')
    selected_course_id = request.GET.get('course')
    selected_batch_id = request.GET.get('batch')

    # For admin dropdowns
    departments = Department.objects.all() if is_admin else None
    teachers = Teacher.objects.filter(dept_id=selected_dept_id) if (is_admin and selected_dept_id) else (Teacher.objects.all() if is_admin else None)

    # Initialize course and batch vars
    courses = None
    batches = None
    user_courses = None
    filtered_batches = None

    # Role-based filtering for courses & batches
    if is_hod or is_teacher:
        if not teacher:
            messages.error(request, "Teacher profile not found.")
            return redirect('login')

        # Courses assigned to the logged-in teacher
        user_courses = Course.objects.filter(teacherbatch__teacher=teacher).distinct()
        course_ids = list(user_courses.values_list('course_id', flat=True))

        if selected_course_id:
            filtered_batches = Batch.objects.filter(course_id=selected_course_id)
        else:
            filtered_batches = Batch.objects.filter(course_id__in=course_ids)

        print("User Courses IDs:", course_ids)
        print("Filtered Batches IDs:", list(filtered_batches.values_list('batch_id', flat=True)))

    elif is_admin:
        if selected_teacher_id:
            courses = Course.objects.filter(teacherbatch__teacher_id=selected_teacher_id).distinct()
        elif selected_dept_id:
            courses = Course.objects.filter(dept_id=selected_dept_id)
        else:
            courses = Course.objects.all()

        batches = Batch.objects.filter(course_id=selected_course_id) if selected_course_id else Batch.objects.all()

    # Build the filtered responses queryset
    responses = StudentFeedbackResponse.objects.none()

    if is_admin:
        responses = all_responses
        if selected_dept_id:
            responses = responses.filter(teacher_batch__department_id=selected_dept_id)
        if selected_teacher_id:
            responses = responses.filter(teacher_batch__teacher_id=selected_teacher_id)
        if selected_course_id:
            responses = responses.filter(teacher_batch__course_id=selected_course_id)
        if selected_batch_id:
            responses = responses.filter(teacher_batch__batch_id=selected_batch_id)

    elif is_hod or is_teacher:
        if not teacher:
            messages.error(request, "Teacher profile not found.")
            return redirect('login')

        responses = StudentFeedbackResponse.objects.filter(teacher_batch__teacher=teacher)
        if selected_course_id:
            responses = responses.filter(teacher_batch__course_id=selected_course_id)
        if selected_batch_id:
            responses = responses.filter(teacher_batch__batch_id=selected_batch_id)

    # Stats calculations
    total_feedback_submissions = responses.values('session_id').distinct().count()
    total_responses_overall = responses.count()
    avg_responses_per_student = round((total_responses_overall / total_feedback_submissions), 2) if total_feedback_submissions else 0

    latest_submission_obj = responses.order_by('-submitted_at').first()
    latest_submission = latest_submission_obj.submitted_at if latest_submission_obj else "--"

    # Group responses by session_id
    grouped = {}
    for r in responses.order_by('submitted_at'):
        grouped.setdefault(r.session_id, []).append(r)

    feedback_sessions = []
    for i, (session_id, session_responses) in enumerate(grouped.items(), start=1):
        first_response = session_responses[0]
        course_info = None
        if first_response.teacher_batch:
            tb = first_response.teacher_batch
            course_info = {
                'course_code': tb.course.code,
                'course_name': tb.course.name,
                'batch': f"{tb.batch.acad_year} - {tb.batch.part}"
            }

        feedback_sessions.append({
            'feedback_number': i,
            'submitted_at': first_response.submitted_at,
            'total_responses': len(session_responses),
            'responses': session_responses,
            'course_info': course_info,
        })

    # Prepare question summaries
    questions_with_responses = []
    questions = FeedbackQuestion.objects.filter(active=True).order_by('q_id')

    for question in questions:
        q_responses = responses.filter(question=question)

        if question.q_type == 'MCQ':
            all_options = FeedbackQOption.objects.filter(q=question).order_by('ans_id')
            option_counts = {opt.answer: 0 for opt in all_options}
            for r in q_responses:
                if r.selected_option:
                    option_counts[r.selected_option.answer] += 1

            questions_with_responses.append({
                'question': question,
                'type': 'MCQ',
                'option_counts': option_counts,
                'total_responses': q_responses.count(),
                'all_options': [opt.answer for opt in all_options],
            })

        elif question.q_type == 'DESC':
            # Only include responses that actually have text
            non_empty_responses = q_responses.filter(
                response_text__isnull=False
            ).exclude(
                response_text__exact=""
            )

            desc_list = [{
                'text': r.response_text,
                'submitted_at': r.submitted_at,
                'feedback_number': r.feedback_number,
                'course_info': f"{r.teacher_batch.course.code}" if r.teacher_batch else "N/A"
            } for r in non_empty_responses]

            questions_with_responses.append({
                'question': question,
                'type': 'DESC',
                'responses': desc_list,
                'total_responses': non_empty_responses.count()
            })

    return render(request, 'admin_response.html', {
        'departments': departments,
        'teachers': teachers,
        'courses': courses,
        'batches': batches,
        'user_courses': user_courses,
        'filtered_batches': filtered_batches,

        'selected_dept_id': int(selected_dept_id) if selected_dept_id else None,
        'selected_teacher_id': int(selected_teacher_id) if selected_teacher_id else None,
        'selected_course_id': int(selected_course_id) if selected_course_id else None,
        'selected_batch_id': int(selected_batch_id) if selected_batch_id else None,

        'total_questions': total_questions,
        'total_feedback_submissions': total_feedback_submissions,
        'latest_submission': latest_submission,
        'avg_responses_per_student': avg_responses_per_student,

        'feedback_sessions': feedback_sessions,
        'questions_with_summary': questions_with_responses,

        'is_admin': is_admin,
        'is_hod': is_hod,
        'is_teacher': is_teacher,
    })
    

def select_teacher_for_feedback(request):
    print("🔥🔥🔥 VIEW IS BEING CALLED 🔥🔥🔥")
 
    # Your existing code here...
    active_teacher_batches = TeacherBatch.objects.filter(
        batch__is_active=True,
        is_active_for_feedback=True
    ).select_related('teacher', 'course', 'batch', 'department')
    
    print(f"🎯 Found {active_teacher_batches.count()} active teacher-batch combinations")
    
    teacher_courses = {}
    for tb in active_teacher_batches:
        teacher = tb.teacher
        if teacher not in teacher_courses:
            teacher_courses[teacher] = []
        teacher_courses[teacher].append(tb)
    
    print(f"🎯 Final teacher_courses dict has {len(teacher_courses)} teachers")
    print(f"🎯 teacher_courses is empty: {not teacher_courses}")
    
    context = {
        'teacher_courses': teacher_courses
    }
    return render(request, 'active_teacher_list.html', context)


from django.shortcuts import get_object_or_404

def student_feedback_form_by_teacher(request, teacher_id):
    """Display feedback form for a selected teacher."""
    teacher = get_object_or_404(Teacher, pk=teacher_id)

    # Get only active questions
    questions = FeedbackQuestion.objects.filter(active=True).order_by('q_id')

    if 'student_feedback_session' not in request.session:
        request.session['student_feedback_session'] = str(uuid.uuid4())

    mcq_questions = []
    desc_questions = []

    for question in questions:
        if question.q_type == 'MCQ':
            options = FeedbackQOption.objects.filter(q=question).order_by('ans_id')
            mcq_questions.append({'question': question, 'options': options})
        elif question.q_type == 'DESC':
            desc_questions.append(question)

    context = {
        'mcq_questions': mcq_questions,
        'desc_questions': desc_questions,
        'session_id': request.session['student_feedback_session'],
        'total_questions': questions.count(),
        'teacher': teacher
    }

    return render(request, 'feedback_form.html', context)

from django.http import JsonResponse
from .models import Course
from .models import Teacher

def get_courses_by_department(request):
    department_id = request.GET.get('department_id')
    courses = Course.objects.filter(dept_id=department_id).values('course_id', 'name')
    return JsonResponse(list(courses), safe=False)

def toggle_feedback_status(request, teacher_id):
    if request.method == 'POST':
        teacher = get_object_or_404(Teacher, pk=teacher_id)
        teacher.fb_active = not teacher.fb_active
        teacher.save()
    return redirect('teacher_list')

@login_required  
def teacher_courses(request, teacher_id):
    teacher = get_object_or_404(Teacher, pk=teacher_id)
    
    # Get teacher's assigned courses where batch is active
    teacher_batches = TeacherBatch.objects.filter(
        teacher=teacher,
        batch__is_active=True  # Only show courses from active batches
    ).select_related('course', 'batch', 'department')
    
    context = {
        'teacher': teacher,
        'teacher_batches': teacher_batches
    }
    return render(request, 'teacher_courses.html', context)

@login_required
def toggle_teacher_course_feedback(request, teacher_batch_id):
    teacher_batch = get_object_or_404(TeacherBatch, pk=teacher_batch_id)
    if request.method == 'POST':
        teacher_batch.is_active_for_feedback = not teacher_batch.is_active_for_feedback
        teacher_batch.save()
        
        status = "activated" if teacher_batch.is_active_for_feedback else "deactivated"
        messages.success(request, f'Feedback for {teacher_batch.course.code} has been {status}!')
    
    return redirect('teacher_courses', teacher_id=teacher_batch.teacher.teacher_id)

def student_feedback_form_by_teacher_course(request, teacher_batch_id):
    """Display feedback form for a specific teacher-course combination."""
    teacher_batch = get_object_or_404(TeacherBatch, pk=teacher_batch_id, is_active_for_feedback=True)
    
    # Get only active questions
    questions = FeedbackQuestion.objects.filter(active=True).order_by('q_id')

    if 'student_feedback_session' not in request.session:
        request.session['student_feedback_session'] = str(uuid.uuid4())

    mcq_questions = []
    desc_questions = []

    for question in questions:
        if question.q_type == 'MCQ':
            options = FeedbackQOption.objects.filter(q=question).order_by('ans_id')
            mcq_questions.append({'question': question, 'options': options})
        elif question.q_type == 'DESC':
            desc_questions.append(question)

    context = {
        'mcq_questions': mcq_questions,
        'desc_questions': desc_questions,
        'session_id': request.session['student_feedback_session'],
        'total_questions': questions.count(),
        'teacher_batch': teacher_batch,  # Pass the teacher-batch object
        'teacher': teacher_batch.teacher,
        'course': teacher_batch.course,
        'batch': teacher_batch.batch
    }

    return render(request, 'feedback_form.html', context)
