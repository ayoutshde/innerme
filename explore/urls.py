from django.urls import path
from . import views

app_name = "explore"
urlpatterns = [
    path("", views.home, name="home"),
    path("test/", views.quiz, name="quiz"),
    path("test/result/", views.result, name="result"),
    path("types/", views.types, name="types"),
    path("types/<str:code>/", views.type_detail, name="type_detail"),
    path("zodiac/", views.zodiac, name="zodiac"),
    path("mood/", views.mood, name="mood"),
    path("journal/", views.journal, name="journal"),
    path("journal/<int:pk>/edit/", views.mood, name="edit"),
    path("journal/<int:pk>/delete/", views.delete, name="delete"),
    path("signup/", views.signup, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("about/", views.about, name="about"),
]
