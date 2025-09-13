from django import forms
from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import Course, Assignment, Student, Submission

User = get_user_model()

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show staff users as teacher options
        self.fields['teacher'].queryset = User.objects.filter(is_staff=True)

class CourseAdmin(admin.ModelAdmin):
    form = CourseForm
    list_display = ('code', 'title', 'teacher')
    list_filter = ('teacher',)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(teacher=request.user)

class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter courses by current teacher (for non-superusers)
        if not self.instance.pk and 'initial' not in kwargs:
            user = getattr(self.request, 'user', None)
            if user and not user.is_superuser:
                self.fields['course'].queryset = Course.objects.filter(teacher=user)

class AssignmentAdmin(admin.ModelAdmin):
    form = AssignmentForm
    list_display = ('title', 'course', 'due_date')
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.request = request
        return form

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show non-staff users as student options
        self.fields['user'].queryset = User.objects.filter(is_staff=False)

class StudentAdmin(admin.ModelAdmin):
    form = StudentForm
   
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Only show students enrolled in teacher's courses
        return qs.filter(courses__teacher=request.user).distinct()

admin.site.register(Course, CourseAdmin)
admin.site.register(Assignment, AssignmentAdmin)
admin.site.register(Student, StudentAdmin)
admin.site.register(Submission)