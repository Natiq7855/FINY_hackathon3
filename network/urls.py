from django.urls import path
from . import views

urlpatterns = [
    path("", views.network_page, name="network"),
    path("data/<int:community_id>/", views.graph_data, name="graph_data"),
]
