from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from .forms import SignUpForm, ProfileForm, OnboardingStep1Form, OnboardingStep2Form, OnboardingStep3Form
from communities.models import Membership, Community
from matchmaking.models import Match
from helpboard.models import HelpRequest


def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.email = form.cleaned_data["email"]
            user.first_name = form.cleaned_data.get("first_name", "")
            user.last_name = form.cleaned_data.get("last_name", "")
            user.save()
            login(request, user)
            return redirect("onboarding_step1")
    else:
        form = SignUpForm()
    return render(request, "accounts/signup.html", {"form": form})


# ── Cognitive Onboarding (3-step quiz) ───────────────────────────────

@login_required
def onboarding_step1(request):
    profile = request.user.profile
    if request.method == "POST":
        form = OnboardingStep1Form(request.POST)
        if form.is_valid():
            profile.intent = form.cleaned_data["intent"]
            profile.save(update_fields=["intent"])
            return redirect("onboarding_step2")
    else:
        form = OnboardingStep1Form(initial={"intent": profile.intent})
    return render(request, "accounts/onboarding/step1.html", {"form": form, "step": 1})


@login_required
def onboarding_step2(request):
    profile = request.user.profile
    if request.method == "POST":
        form = OnboardingStep2Form(request.POST)
        if form.is_valid():
            profile.interests = ", ".join(form.cleaned_data["interests"])
            profile.save(update_fields=["interests"])
            return redirect("onboarding_step3")
    else:
        current = [i.strip() for i in profile.interests.split(",") if i.strip()]
        form = OnboardingStep2Form(initial={"interests": current})
    return render(request, "accounts/onboarding/step2.html", {"form": form, "step": 2})


@login_required
def onboarding_step3(request):
    profile = request.user.profile
    if request.method == "POST":
        form = OnboardingStep3Form(request.POST)
        if form.is_valid():
            profile.communication_style = form.cleaned_data["communication_style"]
            profile.onboarding_complete = True
            profile.save(update_fields=["communication_style", "onboarding_complete"])
            messages.success(request, "Onboarding complete! Welcome to PeerWeave.")
            return redirect("dashboard")
    else:
        form = OnboardingStep3Form(initial={"communication_style": profile.communication_style})
    return render(request, "accounts/onboarding/step3.html", {"form": form, "step": 3})


@login_required
def profile(request):
    profile_obj = request.user.profile
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile_obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("profile")
    else:
        form = ProfileForm(instance=profile_obj)
    return render(request, "accounts/profile.html", {"form": form, "profile": profile_obj})


@login_required
def dashboard(request):
    user = request.user
    memberships = Membership.objects.filter(user=user).select_related("community")
    week_ago = timezone.now() - timedelta(days=7)

    recent_matches = Match.objects.filter(
        Q(user_a=user) | Q(user_b=user),
        created_at__gte=week_ago,
    ).select_related("user_a", "user_b", "community").order_by("-created_at")[:5]

    open_help = HelpRequest.objects.filter(
        community__in=[m.community for m in memberships],
        status="open",
    ).order_by("-created_at")[:5]

    # Community health scores
    community_health = []
    for membership in memberships:
        from communities.services import compute_health_score
        score = compute_health_score(membership.community)
        community_health.append({"community": membership.community, "score": score})

    context = {
        "memberships": memberships,
        "recent_matches": recent_matches,
        "open_help": open_help,
        "community_health": community_health,
    }
    return render(request, "dashboard.html", context)
