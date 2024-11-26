from django.contrib import admin

# Register your models here.
from .models import User, Project, Task, Comment, Team

admin.site.register(User)
admin.site.register(Project)
admin.site.register(Task)
admin.site.register(Comment)
admin.site.register(Team)