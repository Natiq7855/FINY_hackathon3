from django.urls import path
from . import views

urlpatterns = [
    path("insights/<int:community_id>/", views.insights_page, name="ai_insights"),
    path("match-explain/", views.match_explain_api, name="ai_match_explain"),
]
