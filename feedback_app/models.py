from django.db import models
from django.contrib.auth.models import User
# -------------------
# Department
# -------------------
class Department(models.Model):
    dept_id = models.AutoField(primary_key=True)
    dept_name = models.CharField(max_length=100)

    def __str__(self):
        return self.dept_name


# -------------------
# Role
# -------------------
class Role(models.Model):
    role_id = models.AutoField(primary_key=True)
    role_name = models.CharField(max_length=50)

    def __str__(self):
        return self.role_name


# -------------------
# Programme
# -------------------
class Programme(models.Model):
    pgm_id = models.AutoField(primary_key=True)
    pgm_name = models.CharField(max_length=100)
    dept = models.ForeignKey(Department, on_delete=models.CASCADE)
    level = models.CharField(max_length=50)

    def __str__(self):
        return self.pgm_name


# -------------------
# Batch
# -------------------
class Batch(models.Model):
    batch_id = models.AutoField(primary_key=True)
    course = models.ForeignKey('Course', on_delete=models.CASCADE)
    acad_year = models.CharField(max_length=10)
    part = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.acad_year} - {self.part}"


# -------------------
# Teacher
# -------------------
class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)  # <-- Add this line
    teacher_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    dept = models.ForeignKey(Department, on_delete=models.CASCADE)
    designation = models.CharField(max_length=100)
    gender = models.CharField(max_length=10)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    fb_active = models.BooleanField(default=False)

    def __str__(self):
        return self.name

# -------------------
# Course
# -------------------
class Course(models.Model):
    course_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50)
    credit = models.IntegerField()
    dept = models.ForeignKey(Department, on_delete=models.CASCADE)
    pgm = models.ForeignKey(Programme, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
    
    
# -------------------
# Teacher-Batch mapping
# -------------------
class TeacherBatch(models.Model):
    teacher_batch_id = models.AutoField(primary_key=True)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)  # ADD THIS

    def __str__(self):
        return f"{self.teacher.name} - {self.batch.acad_year} - {self.course.code} - {self.department.dept_name}"



# -------------------
# Feedback Setup
# -------------------
class Feedback(models.Model):
    fb_id = models.AutoField(primary_key=True)
    part = models.CharField(max_length=20)
    acad_year = models.CharField(max_length=10)

    def __str__(self):
        return self.fb_id


# -------------------
# Feedback Question Type
# -------------------
class FeedbackQType(models.Model):
    mcq = models.BooleanField(default=True)
    desc = models.TextField()

    def __str__(self):
        return "MCQ" if self.mcq else "Descriptive"


# -------------------
# Feedback Questions
# -------------------
class FeedbackQuestion(models.Model):
    q_id = models.AutoField(primary_key=True)
    q_desc = models.TextField()
    q_type = models.CharField(max_length=20)  # e.g., 'MCQ' or 'DESC'
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.q_desc


# -------------------
# Feedback Question Options
# -------------------
class FeedbackQOption(models.Model):
    q = models.ForeignKey(FeedbackQuestion, on_delete=models.CASCADE)
    ans_id = models.CharField(max_length=10)  # Custom ID (not necessary for options)
    answer = models.CharField(max_length=200)  # The text of the option (e.g., "Excellent")

    def __str__(self):
        return self.answer  # Ensure the option text is returned



# -------------------
# Teacher Feedback Responses
# -------------------
class TeacherFeedbackResponse(models.Model):
    response_id = models.AutoField(primary_key=True)
    teacher_batch = models.ForeignKey(TeacherBatch, on_delete=models.CASCADE)
    fb = models.ForeignKey(Feedback, on_delete=models.CASCADE)
    q = models.ForeignKey(FeedbackQuestion, on_delete=models.CASCADE)
    ans_id = models.CharField(max_length=10, null=True, blank=True)
    ans_desc = models.TextField(null=True, blank=True)
    created_date_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.teacher_batch} - {self.q}"


# Add this new model to your existing models.py


class StudentFeedbackResponse(models.Model):
    response_id = models.AutoField(primary_key=True)
    question = models.ForeignKey(FeedbackQuestion, on_delete=models.CASCADE)
    response_text = models.TextField(blank=True, null=True)  # For descriptive questions
    selected_option = models.ForeignKey(FeedbackQOption, on_delete=models.CASCADE, blank=True, null=True)  # For MCQ
    submitted_at = models.DateTimeField(auto_now_add=True)
    session_id = models.CharField(max_length=100)  # To group responses from same student
    feedback_number = models.IntegerField(default=1)  # Sequential numbering for anonymous feedback
    
    def __str__(self):
        return f"Feedback #{self.feedback_number} - {self.question.q_desc[:30]}..."
    
    class Meta:
        db_table = 'student_feedback_response'
        ordering = ['feedback_number', 'question__q_id']