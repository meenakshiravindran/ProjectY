from django.contrib import admin
from .models import *

admin.site.register(Department)
admin.site.register(Role)
admin.site.register(Teacher)
admin.site.register(Programme)
admin.site.register(Course)
admin.site.register(Batch)
admin.site.register(TeacherBatch)
admin.site.register(Feedback)
admin.site.register(FeedbackQType)
admin.site.register(FeedbackQuestion)
admin.site.register(FeedbackQOption)
admin.site.register(TeacherFeedbackResponse)
