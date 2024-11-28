from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.urls import reverse
from .models import User, Project, Comment, Task, Team
from django.core.exceptions import ObjectDoesNotExist
import json


def register(request):
    if request.method == "POST":
        username = request.POST["username"].strip()
        email = request.POST["email"]

        # Password match confirmation
        password = request.POST["password"]
        confirm_password = request.POST["confirm-password"]

        if password != confirm_password:
            return render(request, "main/register.html", {
                "msg": "Passwords do not match."
            })

        # Attempt to create a new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "main/register.html", {
                "msg": "Username already taken"
            })

        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "main/register.html")


def login_view(request):
    if request.method == "POST":
        username = request.POST["username"].strip()
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication is successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "main/login.html", {
                "msg": "Invalid username and/or password"
            })
    else:
        return render(request, "main/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("login"))


@login_required(login_url="/login")
def index(request):
    username = request.user.username
    teams = Team.objects.filter(member=username).values()

    # Stores ids of the projects related to the user
    project_ids = []

    for team in teams:
        project_ids.append(team["project_id"])

    filter = request.GET.get("filter")

    if filter == "all" or filter is None:
        projects = Project.objects.filter(id__in=project_ids) \
            .order_by("-id")
    elif filter == "completed":
        projects = Project.objects.filter(id__in=project_ids) \
            .filter(is_completed=True) \
            .order_by("-id")
    elif filter == "uncompleted":
        projects = Project.objects.filter(id__in=project_ids) \
            .filter(is_completed=False) \
            .order_by("-id")
    elif filter == "joined":
        projects = Project.objects.filter(id__in=project_ids) \
            .exclude(creator=request.user.username) \
            .order_by("-id")
    elif filter == "created":
        projects = Project.objects.filter(id__in=project_ids) \
            .filter(creator=request.user.username) \
            .order_by("-id")

    return render(request, "main/index.html", {
        "projects": projects,
        "filter": filter
    })


@login_required(login_url="/login")
def project(request, id=None):
    if request.method == "POST":
        creator = request.user.username
        creator_id = request.user.id
        name = request.POST["project-name"]
        description = request.POST["project-description"]

        # Create a new project
        if len(name) > 0:
            project = Project(
                name=name.lower().capitalize(),
                description=description,
                creator=creator,
                creator_id=creator_id,
            )
            project.save()
            project_id = project.id

            # Add the creator as a team member working on the project
            team = Team(
                project=project,
                member=creator,
                role="admin",
            )
            team.save()

            return JsonResponse({
                "projectId": project_id
            })
        else:
            error = JsonResponse({
                "error": "Project name cannot be empty"
            })
            return HttpResponse(error, status=400)
    elif request.method == "DELETE":
        try:
            Project.objects.get(id=id).delete()
        except ObjectDoesNotExist:
            error = JsonResponse({
                "error": "Cannot delete a project that does not exist"
            })
            return HttpResponse(error, status=400)

        return JsonResponse({
            "projectId": id,
        })
    elif request.method == "PUT":
        body_unicode = request.body.decode("utf-8")
        body = json.loads(body_unicode)

        try:
            new_project_name = body["project_name"]
        except KeyError:
            new_project_name = None

        try:
            new_project_description = body["project_description"]
        except KeyError:
            new_project_description = None

        try:
            is_completed = body["isCompleted"]
        except KeyError:
            is_completed = None

        if new_project_name is not None:
            if len(new_project_name) > 0:
                project = Project.objects.get(id=id)
                project.name = new_project_name
                project.save()

                return JsonResponse({
                    "response": "success",
                    "projectName": new_project_name,
                    "elementId": "project-name",
                })
            else:
                error = JsonResponse({
                    "error": "Project name cannot be empty"
                })
                return HttpResponse(error, status=400)

        if new_project_description is not None:
            if len(new_project_description) > 0:
                project = Project.objects.get(id=id)
                project.description = new_project_description
                project.save()

                return JsonResponse({
                    "response": "success",
                    "projectDescription": new_project_description,
                    "elementId": "project-description",
                })
            else:
                error = JsonResponse({
                    "error": "Project description cannot be empty"
                })
                return HttpResponse(error, status=400)

        if is_completed is not None:
            project = Project.objects.get(id=id)
            project.is_completed = is_completed
            project.save()

            success = JsonResponse({
                "success": "project state updated"
            })
            return HttpResponse(success, status=200)

    else:  # request.method == "GET"
        if id != None:
            try:
                project = Project.objects.get(id=id)
                teams = Team.objects.filter(project=project).values()
                assigned = request.GET.get("assigned")
                stage = request.GET.get("stage")

                if assigned == "All" or assigned is None:
                    team_select = "All"
                    if stage == "all" or stage is None:
                        tasks = Task.objects.filter(
                            project_id=id).order_by("-id")
                        task_select = "all"
                    else:
                        tasks = Task.objects.filter(project_id=id) \
                                            .filter(stage=stage) \
                                            .order_by("-id")
                        task_select = stage
                else:
                    team_select = assigned
                    if stage == "all" or stage is None:
                        tasks = Task.objects.filter(project_id=id) \
                                            .filter(assigned_to=assigned) \
                                            .order_by("-id")
                        task_select = "all"
                    else:
                        tasks = Task.objects.filter(project_id=id) \
                                            .filter(assigned_to=assigned) \
                                            .filter(stage=stage) \
                                            .order_by("-id")
                        task_select = stage

                return render(request, "main/project.html", {
                    "project": project,
                    "tasks": tasks,
                    "teams": teams,
                    "team_select": team_select,
                    "task_select": task_select,
                })
            except ObjectDoesNotExist:
                return HttpResponse(status=404)
        else:
            return HttpResponseRedirect(reverse("index"))


@login_required(login_url="/login")
def task(request, id=None):
    if request.method == "POST":
        task_text = request.POST["task-text"]
        project_id = request.POST["project-id"]

        if len(task_text) > 0:
            project = Project.objects.get(id=project_id)

            task = Task(
                project=project,
                task=task_text,
            )
            task.save()
            task_id = task.id

            task = Task.objects.get(id=task_id)

            teams = list(Team.objects.filter(project=project).values())
        else:
            error = JsonResponse({
                "error": "Task cannot be empty"
            })
            return HttpResponse(error, status=400)

        return JsonResponse({
            "response": "success",
            "taskId": task.id,
            "task": task.task,
            "taskStage": task.stage,
            "assigned_to": task.assigned_to,
            "commentNumber": task.comment_count,
            "projectCreator": project.creator,
            "projectTeamLeader": project.team_leader,
            "user": request.user.username,
            "teams": teams,
        })
    elif request.method == "DELETE":
        try:
            Task.objects.get(id=id).delete()
        except ObjectDoesNotExist:
            error = JsonResponse({
                "error": "Cannot delete a task that does not exist"
            })
            return HttpResponse(error, status=400)

        return JsonResponse({
            "taskId": id,
        })
    elif request.method == "PUT":
        body_unicode = request.body.decode("utf-8")
        body = json.loads(body_unicode)
        new_task = body["task"]

        if len(new_task) > 0:
            task = Task.objects.get(id=id)
            task.task = new_task
            task.save()
        else:
            error = JsonResponse({
                "error": "Tasks cannot be empty"
            })
            return HttpResponse(error, status=400)

        return JsonResponse({
            "response": "success",
            "taskText": new_task,
            "taskId": task.id,
            "projectId": task.project_id
        })
    else:  # request.method == "GET"
        return HttpResponseRedirect(reverse("index"))


@login_required(login_url="/login")
def comment(request, id=None):
    if request.method == "POST":
        comment = request.POST["comment"]
        id = request.POST["task-id"]
        creator = request.user.username

        if len(comment) > 0:
            task = Task.objects.get(id=id)

            new_comment = Comment(
                task=task,
                comment=comment,
                creator=creator,
            )
            new_comment.save()
            comment_id = new_comment.id

            cmt = list(Comment.objects.filter(id=comment_id).values())
        else:
            error = JsonResponse({
                "error": "Comment cannot be empty"
            })
            return HttpResponse(error, status=400)

        return JsonResponse({
            "comment": cmt,
            "taskId": task.id,
            "username": request.user.username,
            "creator": creator,
            "commentCount": task.comment_count,
        })
    elif request.method == "DELETE":
        try:
            Comment.objects.get(id=id).delete()
        except ObjectDoesNotExist:
            error = JsonResponse({
                "error": "Cannot delete a comment which does not exist"
            })
            return HttpResponse(error, status=400)

        return JsonResponse({
            "commentId": id,
        })
    elif request.method == "GET":
        try:
            task = Task.objects.get(id=id)

            comments = list(Comment.objects.filter(task_id=task.id).values())
        except ObjectDoesNotExist:
            error = JsonResponse({
                "error": "Unable to get comments with that task id",
            })
            return HttpResponse(error, status=400)

        return JsonResponse({
            "taskText": task.task,
            "taskId": task.id,
            "username": request.user.username,
            "comments": comments,
            "commentCount": task.comment_count,
        })
    elif request.method == "PUT":
        body_unicode = request.body.decode("utf-8")
        body = json.loads(body_unicode)
        new_comment = body["comment"]

        if len(new_comment) > 0:
            comment = Comment.objects.get(id=id)
            comment.comment = new_comment
            comment.save()
        else:
            error = JsonResponse({
                "error": "Comment cannot be empty"
            })
            return HttpResponse(error, status=404)

        return JsonResponse({
            "response": "success",
            "taskId": comment.task_id,
            "commentText": new_comment,
            "commentId": comment.id,
        })


@login_required(login_url="/login")
def stage(request, id):
    if request.method == "PUT":
        body_unicode = request.body.decode("utf-8")
        body = json.loads(body_unicode)
        task_stage = body["taskStage"]

        task = Task.objects.get(id=id)
        task.stage = task_stage
        task.save()

        return JsonResponse({
            "response": "success"
        })


@login_required(login_url="/login")
def team(request, id=None):
    if request.method == "POST":
        username = request.POST["username"].strip().lower()
        project_id = request.POST["project_id"]
        role = request.POST["role"]

        try:
            # Checks if user exist
            _ = User.objects.get(username=username)

            project = Project.objects.get(id=project_id)

            try:
                # Checks if the user is already a part of the team
                _ = Team.objects.filter(project=project).get(member=username)
                error = JsonResponse({
                    "error": f"{username} is already a part of this team"
                })
                return HttpResponse(error, status=400)
            except ObjectDoesNotExist:
                if role == "Team leader":
                    if project.team_leader == "unassigned":
                        project.team_leader = username
                        project.save()
                    else:
                        error = JsonResponse({
                            "error": "This project already has a team leader"
                        })
                        return HttpResponse(error, status=400)

                team = Team(
                    project=project,
                    member=username,
                    role=role,
                )
                team.save()
                team_id = team.id

                new_team = list(Team.objects.filter(id=team_id).values())

                return JsonResponse({
                    "success": f"{username} has been added to the team",
                    "team": new_team,
                    "projectLeader": project.team_leader,
                    "username": request.user.username,
                    "projectCreator": project.creator,
                })
        except ObjectDoesNotExist:
            error = JsonResponse({
                "error": "User does not exist"
            })
            return HttpResponse(error, status=400)
    elif request.method == "PUT":
        body_unicode = request.body.decode("utf-8")
        body = json.loads(body_unicode)
        username = body["username"]
        project_id = body["project_id"]
        role = body["role"]

        try:
            # Checks if user exist
            _ = User.objects.get(username=username)

            project = Project.objects.get(id=project_id)

            if role == "Team leader":
                if project.team_leader == "unassigned":
                    project.team_leader = username
                    project.save()
                else:
                    error = JsonResponse({
                        "error": "This project already has a team leader"
                    })
                    return HttpResponse(error, status=400)
            else:
                if project.team_leader == username:
                    project.team_leader = "unassigned"
                    project.save()

            team = Team.objects.filter(project=project).get(member=username)
            team.role = role
            team.save()

            return JsonResponse({
                "success": f"{username} role as been updated",
                "teamId": team.id
            })
        except ObjectDoesNotExist:
            error = JsonResponse({
                "error": "User does not exist"
            })
            return HttpResponse(error, status=400)
    elif request.method == "DELETE":
        try:
            team = Team.objects.get(id=id)
            project_id = team.project_id
            project = Project.objects.get(id=project_id)
            if team.role == "Team leader":
                project.team_leader = "unassigned"
                project.save()

            team.delete()

        except ObjectDoesNotExist:
            error = JsonResponse({
                "error": "Cannot delete a team member that does not exist"
            })
            return HttpResponse(error, status=400)

        return JsonResponse({
            "teamId": id,
        })


@login_required(login_url="/login")
def assign(request, id=None):
    if request.method == "PUT":
        body_unicode = request.body.decode("utf-8")
        body = json.loads(body_unicode)
        member = body["assign"]

    task = Task.objects.get(id=id)
    task.assigned_to = member
    task.save()

    return JsonResponse({
        "response": "success",
    })


@login_required(login_url="/login")
def comment_count(request):
    if request.method == "POST":
        task_id = request.POST["taskId"]
        comment_count = request.POST["commentCount"]

        task = Task.objects.get(id=task_id)
        task.comment_count = comment_count
        task.save()

        return JsonResponse({
            "response": "success",
            "commentCount": comment_count,
            "taskId": task_id,
        })
