from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from .models import Community, Membership
from .forms import CommunityForm
from .services import compute_health_score


@login_required
def community_list(request):
    all_communities = Community.objects.all()
    my_ids = request.user.memberships.values_list("community_id", flat=True)
    context = {"all_communities": all_communities, "my_ids": list(my_ids)}
    return render(request, "communities/list.html", context)


@login_required
def community_create(request):
    if request.method == "POST":
        form = CommunityForm(request.POST)
        if form.is_valid():
            community = form.save(commit=False)
            community.owner = request.user
            community.save()
            Membership.objects.create(user=request.user, community=community, role="admin")
            messages.success(request, f'Community "{community.name}" created!')
            return redirect("community_detail", pk=community.pk)
    else:
        form = CommunityForm()
    return render(request, "communities/create.html", {"form": form})


@login_required
def community_detail(request, pk):
    community = get_object_or_404(Community, pk=pk)
    members = community.memberships.select_related("user", "user__profile")
    is_member = members.filter(user=request.user).exists()
    health = compute_health_score(community)
    context = {
        "community": community,
        "members": members,
        "is_member": is_member,
        "health": health,
    }
    return render(request, "communities/detail.html", context)


@login_required
@require_POST
def join_community(request, pk):
    community = get_object_or_404(Community, pk=pk)
    membership, created = Membership.objects.get_or_create(user=request.user, community=community)
    if created:
        messages.success(request, f'You joined "{community.name}"!')
    else:
        messages.info(request, "You are already a member.")
    return redirect("community_detail", pk=pk)


@login_required
@require_POST
def leave_community(request, pk):
    community = get_object_or_404(Community, pk=pk)
    Membership.objects.filter(user=request.user, community=community).delete()
    messages.success(request, f'You left "{community.name}".')
    return redirect("community_list")
