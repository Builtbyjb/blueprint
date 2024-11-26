from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("register", views.register, name="register"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("task", views.task, name="task"),
    path("task/<int:id>", views.task, name="task"),
    path("comment", views.comment, name="comment"),
    path("comment/<int:id>", views.comment, name="comment"),
    path("team", views.team, name="team"),
    path("team/<int:id>", views.team, name="team"),
    path("stage/<int:id>", views.stage, name="stage"),
    path("project", views.project, name="project"),
    path("project/<int:id>", views.project, name="project"),
    path("assign/<int:id>", views.assign, name="assign"),
    path("comment_count", views.comment_count, name="comment_count"),
]