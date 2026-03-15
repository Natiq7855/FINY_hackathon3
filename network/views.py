from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from communities.models import Community, Membership
from matchmaking.models import Connection, Interaction
from squads.models import Squad


SQUAD_COLORS = [
    "#6366f1", "#10b981", "#8b5cf6", "#f59e0b", "#3b82f6",
    "#ec4899", "#14b8a6", "#f97316", "#06b6d4", "#84cc16",
]


@login_required
def network_page(request):
    memberships = Membership.objects.filter(user=request.user).select_related("community")
    community_id = request.GET.get("community")
    selected_community = None
    if community_id:
        selected_community = get_object_or_404(Community, pk=community_id)
    elif memberships.exists():
        selected_community = memberships.first().community

    return render(request, "network/graph.html", {
        "memberships": memberships,
        "selected_community": selected_community,
    })


@login_required
def graph_data(request, community_id):
    """JSON endpoint returning nodes and edges for the graph, colored by squad."""
    community = get_object_or_404(Community, pk=community_id)

    if not Membership.objects.filter(user=request.user, community=community).exists():
        return JsonResponse({"error": "Not a member"}, status=403)

    member_ids = list(community.memberships.values_list("user_id", flat=True))

    # Build squad→color mapping
    squads = Squad.objects.filter(community=community, is_active=True)
    user_squad_color = {}
    squad_legend = []
    for i, squad in enumerate(squads):
        color = SQUAD_COLORS[i % len(SQUAD_COLORS)]
        squad_legend.append({"name": squad.name, "color": color})
        for uid in squad.members.values_list("id", flat=True):
            user_squad_color[uid] = color

    # Build nodes
    memberships = community.memberships.select_related("user")
    nodes = []
    connected_ids = set()

    connections = Connection.objects.filter(
        user_a_id__in=member_ids, user_b_id__in=member_ids
    )

    for c in connections:
        connected_ids.add(c.user_a_id)
        connected_ids.add(c.user_b_id)

    for m in memberships:
        u = m.user
        if u.id not in connected_ids:
            color = "#ef4444"  # isolated = red
        else:
            color = user_squad_color.get(u.id, "#94a3b8")  # squad color or gray
        nodes.append({
            "id": u.id,
            "label": u.get_full_name() or u.username,
            "title": f"@{u.username}",
            "isolated": u.id not in connected_ids,
            "color": color,
        })

    # Build edges
    edges = []
    type_colors = {
        "match": "#6366f1",
        "buddy": "#10b981",
        "help": "#f59e0b",
        "chat": "#3b82f6",
    }
    for c in connections:
        edges.append({
            "from": c.user_a_id,
            "to": c.user_b_id,
            "type": c.connection_type,
            "color": type_colors.get(c.connection_type, "#94a3b8"),
            "width": c.weight,
        })

    return JsonResponse({
        "nodes": nodes,
        "edges": edges,
        "squad_legend": squad_legend,
    })


@login_required
def community_heatmap(request):
    """Admin-level dashboard: per-community squad activity heatmap."""
    memberships = Membership.objects.filter(user=request.user).select_related("community")
    cutoff_24h = timezone.now() - timedelta(hours=24)
    cutoff_72h = timezone.now() - timedelta(hours=72)

    communities_data = []
    for membership in memberships:
        community = membership.community
        squads = Squad.objects.filter(community=community, is_active=True)
        squad_rows = []
        for squad in squads:
            member_ids = list(squad.members.values_list("id", flat=True))
            recent = Interaction.objects.filter(
                community=community,
                actor_id__in=member_ids,
                timestamp__gte=cutoff_24h,
            ).count()
            older = Interaction.objects.filter(
                community=community,
                actor_id__in=member_ids,
                timestamp__gte=cutoff_72h,
                timestamp__lt=cutoff_24h,
            ).count()

            if recent > 0:
                status = "green"
            elif older > 0:
                status = "yellow"
            else:
                status = "red"

            squad_rows.append({
                "squad": squad,
                "interactions_24h": recent,
                "interactions_72h": older,
                "status": status,
            })
        communities_data.append({
            "community": community,
            "squads": squad_rows,
        })

    return render(request, "network/heatmap.html", {"communities_data": communities_data})
