"""
Auto-clustering service: groups community members into Squads
based on interest similarity (max 12 members per squad).
"""
from collections import defaultdict
from itertools import combinations

from django.contrib.auth.models import User
from communities.models import Community, Membership
from squads.models import Squad


def _interest_similarity(interests_a: set, interests_b: set) -> float:
    if not interests_a or not interests_b:
        return 0.0
    intersection = interests_a & interests_b
    union = interests_a | interests_b
    return len(intersection) / len(union)  # Jaccard index


def auto_cluster_users(community_id: int) -> list[Squad]:
    """
    1. Get all community members with profiles.
    2. Compute pairwise interest similarity.
    3. Group users by dominant shared interests (greedy clustering).
    4. Create Squad objects with max 12 members.
    Returns list of newly created squads.
    """
    community = Community.objects.get(pk=community_id)
    memberships = Membership.objects.filter(community=community).select_related(
        "user", "user__profile"
    )

    # Build user→interests mapping
    user_interests: dict[int, set] = {}
    user_map: dict[int, User] = {}
    for m in memberships:
        try:
            interests = set(m.user.profile.interests_list())
        except Exception:
            interests = set()
        user_interests[m.user.id] = interests
        user_map[m.user.id] = m.user

    # Skip users already in an active squad for this community
    existing_squad_user_ids = set(
        User.objects.filter(
            squads__community=community, squads__is_active=True
        ).values_list("id", flat=True)
    )
    unassigned_ids = [uid for uid in user_interests if uid not in existing_squad_user_ids]

    if len(unassigned_ids) < 2:
        return []

    # Greedy clustering: pick seed user, pull in most similar users
    remaining = set(unassigned_ids)
    clusters: list[list[int]] = []

    while remaining:
        seed = remaining.pop()
        cluster = [seed]
        seed_interests = user_interests[seed]

        # Score all remaining by similarity to seed
        scored = []
        for uid in remaining:
            sim = _interest_similarity(seed_interests, user_interests[uid])
            scored.append((sim, uid))
        scored.sort(reverse=True)

        for sim, uid in scored:
            if len(cluster) >= Squad.MAX_MEMBERS:
                break
            if sim > 0:  # at least one shared interest
                cluster.append(uid)

        for uid in cluster[1:]:
            remaining.discard(uid)

        clusters.append(cluster)

    # Create Squad objects
    created_squads = []
    for i, cluster_ids in enumerate(clusters):
        # Determine dominant topics from cluster members' interests
        topic_counter: dict[str, int] = defaultdict(int)
        for uid in cluster_ids:
            for interest in user_interests[uid]:
                topic_counter[interest] += 1
        top_topics = sorted(topic_counter, key=topic_counter.get, reverse=True)[:3]

        squad_name = " & ".join(t.title() for t in top_topics) if top_topics else f"Squad {i + 1}"

        squad = Squad.objects.create(
            community=community,
            name=squad_name,
            topic_focus=top_topics,
        )
        squad.members.set([user_map[uid] for uid in cluster_ids])
        created_squads.append(squad)

    return created_squads
