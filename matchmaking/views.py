from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from communities.models import Membership, Community
from .models import Match
from .services import find_best_match, create_match


@login_required
def match_page(request):
    memberships = Membership.objects.filter(user=request.user).select_related("community")
    selected_community = None
    matched_user = None
    match_score = None
    match_obj = None

    community_id = request.GET.get("community") or request.POST.get("community")
    if community_id:
        selected_community = get_object_or_404(Community, pk=community_id)
        if not memberships.filter(community=selected_community).exists():
            messages.error(request, "You are not a member of this community.")
            return redirect("match")

    if request.method == "POST" and selected_community:
        candidate, score = find_best_match(request.user, selected_community)
        if candidate:
            match_obj = create_match(request.user, candidate, selected_community)
            matched_user = candidate
            match_score = score
            messages.success(request, f"Matched with {candidate.username}!")
        else:
            messages.warning(request, "No new peers available in this community right now.")

    my_matches = Match.objects.filter(
        Q(user_a=request.user) | Q(user_b=request.user)
    ).select_related("user_a", "user_b", "community").order_by("-created_at")[:10]

    context = {
        "memberships": memberships,
        "selected_community": selected_community,
        "matched_user": matched_user,
        "match_score": match_score,
        "match_obj": match_obj,
        "my_matches": my_matches,
    }
    return render(request, "matchmaking/match.html", context)


@login_required
def accept_match(request, pk):
    match = get_object_or_404(Match, pk=pk)
    if request.user not in (match.user_a, match.user_b):
        messages.error(request, "Not your match.")
        return redirect("match")
    match.status = "accepted"
    match.save()
    messages.success(request, "Match accepted!")
    return redirect("match")


@login_required
def reject_match(request, pk):
    match = get_object_or_404(Match, pk=pk)
    if request.user not in (match.user_a, match.user_b):
        messages.error(request, "Not your match.")
        return redirect("match")
    match.status = "rejected"
    match.save()
    messages.info(request, "Match declined.")
    return redirect("match")
