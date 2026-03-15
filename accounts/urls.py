from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path("signup/", views.signup, name="signup"),
    path("login/", auth_views.LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("profile/", views.profile, name="profile"),
    path("onboarding/step1/", views.onboarding_step1, name="onboarding_step1"),
    path("onboarding/step2/", views.onboarding_step2, name="onboarding_step2"),
    path("onboarding/step3/", views.onboarding_step3, name="onboarding_step3"),
]
