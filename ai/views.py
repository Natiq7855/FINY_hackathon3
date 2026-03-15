from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.auth.models import User
from communities.models import Community, Membership
from communities.services import compute_health_score
from matchmaking.models import Match
from . import services


@login_required
def insights_page(request, community_id):
    community = get_object_or_404(Community, pk=community_id)
    if not Membership.objects.filter(user=request.user, community=community).exists():
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("You are not a member of this community.")

    health_score = compute_health_score(community)
    member_analysis = services.analyze_members(community)
    health_insights = services.community_insights(community, health_score)

    return render(request, "ai/insights.html", {
        "community": community,
        "health_score": health_score,
        "member_analysis": member_analysis,
        "health_insights": health_insights,
    })


@login_required
def match_explain_api(request):
    """
    AJAX endpoint: explain why the current user and another user are a good match.
    GET params: peer_id (required)
    Returns JSON: {summary, collaboration, ice_breaker}
    """
    peer_id = request.GET.get("peer_id")
    if not peer_id:
        return JsonResponse({"error": "peer_id required"}, status=400)

    peer = get_object_or_404(User, pk=peer_id)

    # Verify both users share at least one community
    my_communities = set(Membership.objects.filter(user=request.user).values_list("community_id", flat=True))
    peer_communities = set(Membership.objects.filter(user=peer).values_list("community_id", flat=True))
    if not my_communities & peer_communities:
        return JsonResponse({"error": "No shared community"}, status=403)

    result = services.explain_peer_match(request.user, peer)
    return JsonResponse(result)
