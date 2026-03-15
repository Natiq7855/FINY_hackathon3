from django.urls import path
from . import views

urlpatterns = [
    path("", views.match_page, name="match"),
    path("<int:pk>/accept/", views.accept_match, name="accept_match"),
    path("<int:pk>/reject/", views.reject_match, name="reject_match"),
]
