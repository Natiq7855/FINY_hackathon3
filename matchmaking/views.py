from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import Q
from communities.models import Membership, Community
from .models import Match
from .services import find_best_match, create_match, compute_match_score, compute_compatibility_score


@login_required
def match_page(request):
    memberships = Membership.objects.filter(user=request.user).select_related("community")
    selected_community = None
    matched_user = None
    match_score = None
    match_obj = None
    suggestions = []

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

    # Build suggestions when a community is selected
    if selected_community:
        already_matched_ids = set()
        matched_pairs = Match.objects.filter(
            Q(user_a=request.user) | Q(user_b=request.user),
            community=selected_community,
        ).values_list("user_a_id", "user_b_id")
        for a_id, b_id in matched_pairs:
            already_matched_ids.add(a_id)
            already_matched_ids.add(b_id)
        already_matched_ids.discard(request.user.id)

        peers = (
            selected_community.memberships
            .exclude(user=request.user)
            .select_related("user", "user__profile")
        )

        try:
            my_interests = set(request.user.profile.interests_list())
            my_skills = set(request.user.profile.skills_list())
        except Exception:
            my_interests = set()
            my_skills = set()

        for m in peers:
            peer = m.user
            try:
                peer_interests = set(peer.profile.interests_list())
                peer_skills = set(peer.profile.skills_list())
            except Exception:
                peer_interests = set()
                peer_skills = set()

            shared_interests = my_interests & peer_interests
            shared_skills = my_skills & peer_skills
            match_pts = compute_match_score(request.user, peer, selected_community)
            compat = compute_compatibility_score(request.user, peer)

            suggestions.append({
                "user": peer,
                "shared_interests": sorted(shared_interests),
                "shared_skills": sorted(shared_skills),
                "match_score": match_pts,
                "compatibility": round(compat * 100),
                "already_matched": peer.id in already_matched_ids,
            })

        suggestions.sort(key=lambda s: s["match_score"], reverse=True)

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
        "suggestions": suggestions,
    }
    return render(request, "matchmaking/match.html", context)


@login_required
@require_POST
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
@require_POST
def reject_match(request, pk):
    match = get_object_or_404(Match, pk=pk)
    if request.user not in (match.user_a, match.user_b):
        messages.error(request, "Not your match.")
        return redirect("match")
    match.status = "rejected"
    match.save()
    messages.info(request, "Match declined.")
    return redirect("match")
