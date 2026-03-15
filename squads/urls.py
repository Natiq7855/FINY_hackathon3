from django.urls import path
from . import views

urlpatterns = [
    path("", views.squad_list, name="squad_list"),
    path("<int:pk>/", views.squad_detail, name="squad_detail"),
    path("cluster/<int:community_id>/", views.run_clustering, name="run_clustering"),
]
