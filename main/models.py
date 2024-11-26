from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    pass

    def __str__(self):
        return f"{self.id}: {self.username}"

class Project(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=200)
    is_completed = models.BooleanField(default=False)
    creator = models.CharField(max_length=100)
    creator_id = models.IntegerField()
    team_leader = models.CharField(max_length=100, default="unassigned")

    def __str__(self):
        return f"{self.id}: {self.name} by {self.creator}"

class Task(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    task = models.CharField(max_length=200)
    assigned_to = models.CharField(max_length=100, default="unassigned")
    stage = models.CharField(max_length=100, default="to-do")
    comment_count = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.id}: {self.task} ->  project {self.project_id}"

class Comment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    comment = models.CharField(max_length=200)
    creator =  models.CharField(max_length=100)

    def __str__(self):
        return f"{self.id}: {self.comment} -> task {self.task_id}"

class Team(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    member = models.CharField(max_length=100)
    role = models.CharField(max_length=100, default="Team member")

    def __str__(self):
        return f"{self.id}: {self.member}, role is {self.role} -> project {self.project_id}"
