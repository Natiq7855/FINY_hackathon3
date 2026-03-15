from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponseForbidden
from django.contrib import messages
from communities.models import Community, Membership
from .models import Squad
from .services.auto_cluster import auto_cluster_users


@login_required
def squad_list(request):
    user_squads = Squad.objects.filter(members=request.user, is_active=True).select_related("community")
    return render(request, "squads/list.html", {"squads": user_squads})


@login_required
def squad_detail(request, pk):
    squad = get_object_or_404(Squad, pk=pk, is_active=True)
    is_member = squad.members.filter(pk=request.user.pk).exists()
    if not is_member:
        return HttpResponseForbidden("You are not a member of this squad.")
    agent_actions = squad.agent_actions.order_by("-executed_at")[:10]
    return render(request, "squads/detail.html", {
        "squad": squad,
        "is_member": is_member,
        "members": squad.members.select_related("profile"),
        "agent_actions": agent_actions,
    })


@login_required
@require_POST
def run_clustering(request, community_id):
    community = get_object_or_404(Community, pk=community_id)
    membership = Membership.objects.filter(user=request.user, community=community).first()
    if not membership:
        messages.error(request, "You are not a member of this community.")
        return redirect("community_list")
    if membership.role != "admin" and community.owner != request.user:
        messages.error(request, "Only community admins can run clustering.")
        return redirect("community_detail", pk=community_id)
    created = auto_cluster_users(community_id)
    if created:
        messages.success(request, f"{len(created)} squad(s) created!")
    else:
        messages.info(request, "No new squads needed — all members are already assigned.")
    return redirect("community_detail", pk=community_id)
