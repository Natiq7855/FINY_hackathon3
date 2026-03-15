from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from communities.models import Membership, Community
from matchmaking.models import Connection, Interaction
from .models import HelpRequest, HelpResponse
from .forms import HelpRequestForm, HelpResponseForm


def find_experts(help_request):
    """Find users in the same community whose skills overlap with the request tags."""
    tags = set(help_request.tags_list())
    if not tags:
        return []

    members = (
        Membership.objects.filter(community=help_request.community)
        .exclude(user=help_request.author)
        .select_related("user", "user__profile")
    )

    experts = []
    for membership in members:
        try:
            skills = set(membership.user.profile.skills_list())
        except Exception:
            skills = set()
        overlap = len(tags & skills)
        if overlap > 0:
            experts.append((membership.user, overlap))

    experts.sort(key=lambda x: -x[1])
    return [u for u, _ in experts[:5]]


@login_required
def help_list(request):
    memberships = Membership.objects.filter(user=request.user).values_list("community_id", flat=True)
    community_id = request.GET.get("community")
    selected_community = None

    if community_id:
        selected_community = get_object_or_404(Community, pk=community_id)
        requests = HelpRequest.objects.filter(community=selected_community)
    else:
        requests = HelpRequest.objects.filter(community_id__in=memberships)

    status_filter = request.GET.get("status", "")
    if status_filter in ("open", "solved"):
        requests = requests.filter(status=status_filter)

    requests = requests.select_related("author", "community").order_by("-created_at")
    my_communities = Community.objects.filter(id__in=memberships)

    context = {
        "requests": requests,
        "my_communities": my_communities,
        "selected_community": selected_community,
        "status_filter": status_filter,
    }
    return render(request, "helpboard/list.html", context)


@login_required
def help_create(request):
    memberships = Membership.objects.filter(user=request.user).select_related("community")
    if request.method == "POST":
        form = HelpRequestForm(request.POST)
        community_id = request.POST.get("community")
        community = get_object_or_404(Community, pk=community_id) if community_id else None
        if form.is_valid() and community:
            help_req = form.save(commit=False)
            help_req.author = request.user
            help_req.community = community
            help_req.save()
            messages.success(request, "Help request posted! Experts have been notified.")
            return redirect("help_detail", pk=help_req.pk)
    else:
        form = HelpRequestForm()
        community_id = request.GET.get("community")
        community = None
        if community_id:
            community = get_object_or_404(Community, pk=community_id)

    return render(request, "helpboard/create.html", {
        "form": form,
        "memberships": memberships,
        "selected_community_id": community_id if community_id else "",
    })


@login_required
def help_detail(request, pk):
    help_req = get_object_or_404(HelpRequest, pk=pk)
    responses = help_req.responses.select_related("helper")
    experts = find_experts(help_req)

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "respond":
            form = HelpResponseForm(request.POST)
            if form.is_valid():
                resp = form.save(commit=False)
                resp.request = help_req
                resp.helper = request.user
                resp.save()
                # Create a help connection
                Connection.objects.get_or_create(
                    user_a=request.user, user_b=help_req.author,
                    defaults={"connection_type": "help", "weight": 1},
                )
                Interaction.objects.create(
                    actor=request.user, target=help_req.author,
                    community=help_req.community, interaction_type="help"
                )
                messages.success(request, "Response posted!")
                return redirect("help_detail", pk=pk)
        elif action == "solve" and request.user == help_req.author:
            help_req.status = "solved"
            help_req.save()
            messages.success(request, "Marked as solved!")
            return redirect("help_detail", pk=pk)
    else:
        form = HelpResponseForm()

    return render(request, "helpboard/detail.html", {
        "help_req": help_req,
        "responses": responses,
        "experts": experts,
        "form": form,
    })
