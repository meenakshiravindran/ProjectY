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
from .models import FeedbackQuestion, FeedbackQOption, StudentFeedbackResponse
import uuid
import json

def student_feedback_form(request):
    """Display feedback form to students (no login required)"""
    # Get only active questions
    questions = FeedbackQuestion.objects.filter(active=True).order_by('q_id')
    
    if not questions.exists():
        messages.info(request, "No feedback questions are available at the moment.")
        return render(request, 'student_feedback/no_questions.html')
    
    # Generate a unique session ID for this feedback submission
    if 'student_feedback_session' not in request.session:
        request.session['student_feedback_session'] = str(uuid.uuid4())
    
    # Get MCQ questions with their options
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
            
            # Check if feedback already submitted for this session
            existing_responses = StudentFeedbackResponse.objects.filter(session_id=session_id)
            if existing_responses.exists():
                return JsonResponse({'success': False, 'error': 'Feedback already submitted from this session.'})
            
            # Parse form data
            responses_saved = 0
            questions = FeedbackQuestion.objects.filter(active=True)
            
            for question in questions:
                if question.q_type == 'MCQ':
                    option_id = request.POST.get(f'question_{question.q_id}')
                    if option_id:
                        try:
                            option = FeedbackQOption.objects.get(id=option_id, q=question)
                            StudentFeedbackResponse.objects.create(
                                question=question,
                                selected_option=option,
                                session_id=session_id
                            )
                            responses_saved += 1
                        except FeedbackQOption.DoesNotExist:
                            continue
                
                elif question.q_type == 'DESC':
                    response_text = request.POST.get(f'question_{question.q_id}', '').strip()
                    if response_text:
                        StudentFeedbackResponse.objects.create(
                            question=question,
                            response_text=response_text,
                            session_id=session_id
                        )
                        responses_saved += 1
            
            if responses_saved > 0:
                # Clear the session after successful submission
                if 'student_feedback_session' in request.session:
                    del request.session['student_feedback_session']
                
                return JsonResponse({
                    'success': True, 
                    'message': f'Thank you! Your feedback has been submitted successfully. ({responses_saved} responses recorded)'
                })
            else:
                return JsonResponse({
                    'success': False, 
                    'error': 'Please answer at least one question before submitting.'
                })
                
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'An error occurred: {str(e)}'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@login_required
def admin_student_feedback_responses(request):
    """Admin view to see all student feedback responses"""
    if not request.user.is_staff:
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('login')
    
    # Get all student responses grouped by question
    questions_with_responses = []
    questions = FeedbackQuestion.objects.filter(active=True).order_by('q_id')
    
    for question in questions:
        responses = StudentFeedbackResponse.objects.filter(question=question).order_by('submitted_at')
        
        if question.q_type == 'MCQ':
            # Group MCQ responses by option
            option_counts = {}
            for response in responses:
                if response.selected_option:
                    option_text = response.selected_option.answer
                    option_counts[option_text] = option_counts.get(option_text, 0) + 1
            
            questions_with_responses.append({
                'question': question,
                'type': 'MCQ',
                'option_counts': option_counts,
                'total_responses': responses.count()
            })
        
        elif question.q_type == 'DESC':
            # Get all descriptive responses
            desc_responses = []
            for response in responses:
                if response.response_text:
                    desc_responses.append({
                        'text': response.response_text,
                        'submitted_at': response.submitted_at
                    })
            
            questions_with_responses.append({
                'question': question,
                'type': 'DESC',
                'responses': desc_responses,
                'total_responses': len(desc_responses)
            })
    
    # Get total unique sessions (students who submitted)
    total_sessions = StudentFeedbackResponse.objects.values('session_id').distinct().count()
    
    context = {
        'questions_with_responses': questions_with_responses,
        'total_questions': questions.count(),
        'total_student_sessions': total_sessions
    }
    
    return render(request, 'admin_responses.html', context)

# Add these views to your existing views.py

from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import FeedbackQuestion, FeedbackQOption, StudentFeedbackResponse
import uuid
import json

def student_feedback_form(request):
    """Display feedback form to students (no login required)"""
    # Get only active questions
    questions = FeedbackQuestion.objects.filter(active=True).order_by('q_id')
    
    if not questions.exists():
        messages.info(request, "No feedback questions are available at the moment.")
        return render(request, 'student_feedback/no_questions.html')
    
    # Generate a unique session ID for this feedback submission
    if 'student_feedback_session' not in request.session:
        request.session['student_feedback_session'] = str(uuid.uuid4())
    
    # Get MCQ questions with their options
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
        'mcq_questions': mcq_questions,
        'desc_questions': desc_questions,
        'session_id': request.session['student_feedback_session'],
        'total_questions': questions.count()
    }
    return render(request, 'student_feedback/feedback_form.html', context)


# Add these views to your existing views.py

from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import FeedbackQuestion, FeedbackQOption, StudentFeedbackResponse
import uuid
import json

def student_feedback_form(request):
    """Display feedback form to students (no login required)"""
    # Get only active questions
    questions = FeedbackQuestion.objects.filter(active=True).order_by('q_id')
    
    if not questions.exists():
        messages.info(request, "No feedback questions are available at the moment.")
        return render(request, 'student_feedback/no_questions.html')
    
    # Generate a unique session ID for this feedback submission
    if 'student_feedback_session' not in request.session:
        request.session['student_feedback_session'] = str(uuid.uuid4())
    
    # Get MCQ questions with their options
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
            
            # Check if feedback already submitted for this session
            existing_responses = StudentFeedbackResponse.objects.filter(session_id=session_id)
            if existing_responses.exists():
                return JsonResponse({'success': False, 'error': 'Feedback already submitted from this session.'})
            
            # Get all active questions
            questions = FeedbackQuestion.objects.filter(active=True)
            unanswered_questions = []
            responses_to_save = []
            
            # Validate all questions are answered
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
                    if not response_text:
                        unanswered_questions.append(f"Question {question.q_id}")
                    else:
                        responses_to_save.append({
                            'question': question,
                            'response_text': response_text,
                            'session_id': session_id
                        })
            
            # If there are unanswered questions, return error
            if unanswered_questions:
                return JsonResponse({
                    'success': False, 
                    'error': f'Please answer all questions. Missing answers for: {", ".join(unanswered_questions)}'
                })
            
            # Get feedback number for this submission (sequential numbering)
            feedback_count = StudentFeedbackResponse.objects.values('session_id').distinct().count()
            feedback_number = feedback_count + 1
            
            # Save all responses
            for response_data in responses_to_save:
                StudentFeedbackResponse.objects.create(
                    question=response_data['question'],
                    selected_option=response_data.get('selected_option'),
                    response_text=response_data.get('response_text'),
                    session_id=session_id,
                    feedback_number=feedback_number  # We'll add this field to model
                )
            
            # Clear the session after successful submission
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
    """Admin view to see all student feedback responses organized by feedback number"""
    if not request.user.is_staff:
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('login')
    
    # Get all feedback responses grouped by feedback_number (student)
    feedback_sessions = []
    unique_feedback_numbers = StudentFeedbackResponse.objects.values('feedback_number').distinct().order_by('feedback_number')
    
    for feedback_data in unique_feedback_numbers:
        feedback_number = feedback_data['feedback_number']
        responses = StudentFeedbackResponse.objects.filter(feedback_number=feedback_number).order_by('question__q_id')
        
        if responses.exists():
            feedback_sessions.append({
                'feedback_number': feedback_number,
                'responses': responses,
                'submitted_at': responses.first().submitted_at,
                'total_responses': responses.count()
            })
    
    # Get summary statistics
    questions_with_summary = []
    questions = FeedbackQuestion.objects.filter(active=True).order_by('q_id')
    
    for question in questions:
        responses = StudentFeedbackResponse.objects.filter(question=question)
        
        if question.q_type == 'MCQ':
            # Group MCQ responses by option
            option_counts = {}
            total_responses = 0
            for response in responses:
                if response.selected_option:
                    option_text = response.selected_option.answer
                    option_counts[option_text] = option_counts.get(option_text, 0) + 1
                    total_responses += 1
            
            questions_with_summary.append({
                'question': question,
                'type': 'MCQ',
                'option_counts': option_counts,
                'total_responses': total_responses
            })
        
        elif question.q_type == 'DESC':
            # Get all descriptive responses
            desc_responses = []
            for response in responses:
                if response.response_text:
                    desc_responses.append({
                        'text': response.response_text,
                        'feedback_number': response.feedback_number,
                        'submitted_at': response.submitted_at
                    })
            
            questions_with_summary.append({
                'question': question,
                'type': 'DESC',
                'responses': desc_responses,
                'total_responses': len(desc_responses)
            })
    
    context = {
        'feedback_sessions': feedback_sessions,
        'questions_with_summary': questions_with_summary,
        'total_questions': questions.count(),
        'total_feedback_submissions': len(feedback_sessions)
    }
    
    return render(request, 'admin_response.html', context)


