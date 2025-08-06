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
    total_responses = StudentFeedbackResponse.objects.count()
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
    rating_options = ['Excellent', 'Very Good', 'Good', 'Average', 'Poor']
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
        'total_responses': total_responses,
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

def get_teacher_dashboard_data(teacher):
    """Generate comprehensive teacher dashboard data"""
    
    # Teacher's courses
    teacher_batches = TeacherBatch.objects.filter(teacher=teacher).select_related(
        'course', 'batch', 'department'
    )
    
    teacher_courses_count = teacher_batches.count()
    
    # Teacher's responses count
    teacher_responses_count = StudentFeedbackResponse.objects.filter(
        teacher=teacher
    ).count()
    
    # Calculate average rating for this teacher
    # This assumes you have a rating system - adjust based on your actual implementation
    rating_responses = StudentFeedbackResponse.objects.filter(
        teacher=teacher,
        selected_option__isnull=False
    ).select_related('selected_option')
    
    # Map rating options to numeric values (adjust based on your system)
    rating_map = {
        'excellent': 5,
        'very good': 4,
        'good': 3,
        'average': 2,
        'poor': 1
    }
    
    total_rating = 0
    rating_count = 0
    feedback_distribution = defaultdict(int)
    
    for response in rating_responses:
        option_text = response.selected_option.answer.lower()
        for key, value in rating_map.items():
            if key in option_text:
                total_rating += value
                rating_count += 1
                feedback_distribution[response.selected_option.answer] += 1
                break
    
    teacher_avg_rating = total_rating / rating_count if rating_count > 0 else 0
    
    # Unique students (based on session_id)
    unique_students = StudentFeedbackResponse.objects.filter(
        teacher=teacher
    ).values('session_id').distinct().count()
    
    # Feedback distribution for charts
    teacher_feedback_labels = list(feedback_distribution.keys())
    teacher_feedback_counts = list(feedback_distribution.values())
    
    # Course-wise performance
    course_performance = []
    course_labels = []
    course_ratings = []
    
    for batch in teacher_batches:
        course_responses = StudentFeedbackResponse.objects.filter(
            teacher=teacher,
            # You might need to add a way to link responses to specific courses
        ).select_related('selected_option')
        
        # Calculate average for this course
        course_total = 0
        course_count = 0
        response_count = 0
        
        for response in course_responses:
            response_count += 1
            if response.selected_option:
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
            'response_count': response_count,
            'avg_rating': course_avg
        }
        course_performance.append(course_info)
        
        # For chart
        course_labels.append(batch.course.code)
        course_ratings.append(course_avg)
    
    return {
        'teacher_courses_count': teacher_courses_count,
        'teacher_responses_count': teacher_responses_count,
        'teacher_avg_rating': teacher_avg_rating,
        'unique_students': unique_students,
        'teacher_feedback_labels': json.dumps(teacher_feedback_labels),
        'teacher_feedback_counts': json.dumps(teacher_feedback_counts),
        'course_labels': json.dumps(course_labels),
        'course_ratings': json.dumps(course_ratings),
        'teacher_courses': course_performance,
    }

# Optional: Helper function to get rating value from option text
def get_rating_value(option_text):
    """Convert option text to numeric rating"""
    option_lower = option_text.lower()
    rating_map = {
        'excellent': 5,
        'very good': 4,
        'good': 3,
        'average': 2,
        'poor': 1
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

    return render(request, 'course_list.html', {
        'courses': courses,
        'departments': departments,
        'selected_dept': selected_dept,
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

    if selected_dept_id:
        assignments = assignments.filter(department__dept_id=selected_dept_id)

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

    departments = Department.objects.all()

    return render(request, 'teacher_batch_list.html', {
        'assignments': grouped_list,
        'departments': departments,
        'selected_dept_id': selected_dept_id,
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


@csrf_exempt
def submit_student_feedback(request):
    """Handle student feedback submission"""
    if request.method == 'POST':
        try:
            session_id = request.session.get('student_feedback_session')
            if not session_id:
                return JsonResponse({'success': False, 'error': 'Session expired. Please refresh the page.'})

            # Prevent duplicate submissions
            existing_responses = StudentFeedbackResponse.objects.filter(session_id=session_id)
            if existing_responses.exists():
                return JsonResponse({'success': False, 'error': 'Feedback already submitted from this session.'})

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

            # Generate feedback number
            feedback_count = StudentFeedbackResponse.objects.values('session_id').distinct().count()
            feedback_number = feedback_count + 1

            teacher_id = request.POST.get('teacher_id')
            teacher = Teacher.objects.filter(pk=teacher_id).first() if teacher_id else None

            # Save responses
            for response_data in responses_to_save:
                StudentFeedbackResponse.objects.create(
                    question=response_data['question'],
                    selected_option=response_data.get('selected_option'),
                    response_text=response_data.get('response_text'),
                    session_id=session_id,
                    feedback_number=feedback_number,
                    teacher=teacher
                )

            # Clear session
            if 'student_feedback_session' in request.session:
                del request.session['student_feedback_session']

            return JsonResponse({
                'success': True,
                'message': f'Thank you! Your feedback has been submitted successfully. (Feedback #{feedback_number})'
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': f'An error occurred: {str(e)}'})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@login_required
def admin_student_feedback_responses(request):
    user = request.user
    is_admin = user.is_staff

    # 🔹 Global stats (for cards)
    total_questions = FeedbackQuestion.objects.filter(active=True).count()
    all_responses = StudentFeedbackResponse.objects.all()
    total_feedback_submissions = all_responses.values('session_id').distinct().count()

    # Avg responses
    total_responses = all_responses.count()
    total_sessions = total_feedback_submissions
    avg_responses_global = round(total_responses / total_sessions, 2) if total_sessions else 0

    # Latest submission
    latest_submission_obj = all_responses.order_by('-submitted_at').first()
    latest_submission = latest_submission_obj.submitted_at if latest_submission_obj else "--"

    # 🔹 Filters
    selected_dept_id = request.GET.get('department')
    selected_teacher_id = request.GET.get('teacher')

    departments = Department.objects.all()
    teachers = Teacher.objects.filter(dept_id=selected_dept_id) if selected_dept_id else Teacher.objects.all()
    
    # 🔹 Filtered responses (for display)
    responses = StudentFeedbackResponse.objects.none()

    if is_admin:
        if selected_teacher_id:
            responses = StudentFeedbackResponse.objects.filter(teacher_id=selected_teacher_id)
        elif selected_dept_id:
            responses = StudentFeedbackResponse.objects.filter(teacher__dept_id=selected_dept_id)
        else:
            responses = all_responses  # default to all responses
    else:
        try:
            teacher = Teacher.objects.get(user=user)
            responses = StudentFeedbackResponse.objects.filter(teacher=teacher)
        except Teacher.DoesNotExist:
            messages.error(request, "Teacher not found.")
            return redirect('login')

    # 🔹 Group by session for display
    grouped = {}
    for response in responses:
        grouped.setdefault(response.session_id, []).append(response)

    feedback_sessions = []
    for i, (session_id, session_responses) in enumerate(grouped.items(), start=1):
        feedback_sessions.append({
            'feedback_number': i,
            'submitted_at': session_responses[0].submitted_at,
            'total_responses': len(session_responses),
            'responses': session_responses,
        })

    # 🔹 Summary tab (filtered)
    questions_with_responses = []
    questions = FeedbackQuestion.objects.filter(active=True).order_by('q_id')

    for question in questions:
        q_responses = responses.filter(question=question)

        if question.q_type == 'MCQ':
            # Fetch all possible options for the question
            all_options = FeedbackQOption.objects.filter(q=question).order_by('ans_id')
            
            # Initialize all options with 0 count
            option_counts = {opt.answer: 0 for opt in all_options}

            # Count actual responses
            for r in q_responses:
                if r.selected_option:
                    key = r.selected_option.answer
                    option_counts[key] += 1

            questions_with_responses.append({
                'question': question,
                'type': 'MCQ',
                'option_counts': option_counts,
                'total_responses': q_responses.count(),
                'all_options': [opt.answer for opt in all_options],  # <- for template use
            })

        elif question.q_type == 'DESC':
            questions_with_responses.append({
                'question': question,
                'type': 'DESC',
                'responses': [{
                    'text': r.response_text,
                    'submitted_at': r.submitted_at,
                    'feedback_number': r.feedback_number
                } for r in q_responses if r.response_text],
                'total_responses': q_responses.count()
            })

    avg_responses = round(responses.count() / len(grouped), 2) if grouped else 0

    context = {
        'departments': departments,
        'teachers': teachers,
        'selected_dept_id': int(selected_dept_id) if selected_dept_id else None,
        'selected_teacher_id': int(selected_teacher_id) if selected_teacher_id else None,

        # Cards - global
        'total_questions': total_questions,
        'total_feedback_submissions': total_feedback_submissions,
        'avg_responses_per_student': avg_responses_global,
        'latest_submission': latest_submission,

        # Tabs - filtered
        'feedback_sessions': feedback_sessions,
        'questions_with_summary': questions_with_responses,
    }

    return render(request, 'admin_response.html', context)

def select_teacher_for_feedback(request):
    """Display list of teachers with fb_active=True for students to choose."""
    teachers = Teacher.objects.filter(fb_active=True)
    return render(request, 'active_teacher_list.html', {'teachers': teachers})

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

def select_teacher_for_feedback(request):
    """Display list of teachers with fb_active=True for students to choose."""
    teachers = Teacher.objects.filter(fb_active=True)
    return render(request, 'active_teacher_list.html',{'teachers':teachers})