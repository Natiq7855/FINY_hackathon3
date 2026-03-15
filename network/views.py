from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from communities.models import Community, Membership
from matchmaking.models import Connection


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
    """JSON endpoint returning nodes and edges for the graph."""
    community = get_object_or_404(Community, pk=community_id)

    # Check user is member
    if not Membership.objects.filter(user=request.user, community=community).exists():
        return JsonResponse({"error": "Not a member"}, status=403)

    member_ids = list(community.memberships.values_list("user_id", flat=True))

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
        nodes.append({
            "id": u.id,
            "label": u.get_full_name() or u.username,
            "title": f"@{u.username}",
            "isolated": u.id not in connected_ids,
            "color": "#ef4444" if u.id not in connected_ids else "#6366f1",
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

    return JsonResponse({"nodes": nodes, "edges": edges})
