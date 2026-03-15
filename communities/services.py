from django.utils import timezone
from datetime import timedelta


def compute_health_score(community):
    """
    Compute a health score (0-100) for a community.
    Formula: 0.3*activity + 0.3*connections + 0.2*helpSolved - 0.2*isolationPenalty
    """
    from matchmaking.models import Connection, Interaction
    from helpboard.models import HelpRequest

    week_ago = timezone.now() - timedelta(days=7)
    members = community.memberships.select_related("user")
    total = members.count()
    if total == 0:
        return 0

    # 1. Activity: users with interactions in last 7 days / total
    active_users = (
        Interaction.objects.filter(community=community, timestamp__gte=week_ago)
        .values("actor")
        .distinct()
        .count()
    )
    activity_ratio = min(active_users / total, 1.0) * 100

    # 2. Connections per member (normalised)
    member_ids = members.values_list("user_id", flat=True)
    connections_count = Connection.objects.filter(
        user_a_id__in=member_ids
    ).filter(user_b_id__in=member_ids).count()
    max_connections = total * (total - 1) / 2 if total > 1 else 1
    connection_ratio = min(connections_count / max_connections, 1.0) * 100

    # 3. Help solved ratio
    total_requests = HelpRequest.objects.filter(community=community).count()
    solved_requests = HelpRequest.objects.filter(community=community, status="solved").count()
    help_ratio = (solved_requests / total_requests * 100) if total_requests > 0 else 50

    # 4. Isolation penalty: users with zero connections
    connected_users = set(
        Connection.objects.filter(user_a_id__in=member_ids)
        .values_list("user_a_id", flat=True)
    ) | set(
        Connection.objects.filter(user_b_id__in=member_ids)
        .values_list("user_b_id", flat=True)
    )
    isolated = total - len(connected_users.intersection(set(member_ids)))
    isolation_ratio = (isolated / total) * 100

    score = (
        0.3 * activity_ratio
        + 0.3 * connection_ratio
        + 0.2 * help_ratio
        - 0.2 * isolation_ratio
    )
    return max(0, min(100, round(score, 1)))
