from django.urls import path
from . import views

urlpatterns = [
    path("", views.help_list, name="help_list"),
    path("create/", views.help_create, name="help_create"),
    path("<int:pk>/", views.help_detail, name="help_detail"),
]
