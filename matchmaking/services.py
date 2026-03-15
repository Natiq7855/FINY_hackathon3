from django.db.models import Q
from .models import Match, Connection, Interaction, BuddyAssignment


def compute_match_score(user, candidate, community=None):
    """
    Score = shared_interests*2 + shared_skills*1 + timezone_match*1
    """
    try:
        p1 = user.profile
        p2 = candidate.profile
    except Exception:
        return 0

    interests_a = set(p1.interests_list())
    interests_b = set(p2.interests_list())
    skills_a = set(p1.skills_list())
    skills_b = set(p2.skills_list())

    shared_interests = len(interests_a & interests_b)
    shared_skills = len(skills_a & skills_b)
    timezone_match = 1 if p1.timezone and p1.timezone == p2.timezone else 0

    return shared_interests * 2 + shared_skills * 1 + timezone_match * 1


def find_best_match(user, community):
    """
    Find the best unmatched peer in the community for `user`.
    Returns (candidate, score) or (None, 0).
    """
    from communities.models import Membership

    member_ids = Membership.objects.filter(community=community).exclude(
        user=user
    ).values_list("user_id", flat=True)

    # Exclude already matched users
    already_matched_ids = set(
        Match.objects.filter(
            Q(user_a=user) | Q(user_b=user), community=community
        ).values_list("user_a_id", "user_b_id")
    )
    flat_matched = set()
    for pair in already_matched_ids:
        flat_matched.update(pair)
    flat_matched.discard(user.id)

    candidates = (
        community.memberships.exclude(user=user)
        .exclude(user_id__in=flat_matched)
        .select_related("user", "user__profile")
    )

    best_candidate = None
    best_score = -1

    for membership in candidates:
        candidate = membership.user
        score = compute_match_score(user, candidate, community)
        if score > best_score:
            best_score = score
            best_candidate = candidate

    return best_candidate, best_score


def create_match(user_a, user_b, community):
    """Create a Match and a Connection, log Interactions."""
    match = Match.objects.create(user_a=user_a, user_b=user_b, community=community)

    Connection.objects.get_or_create(
        user_a=user_a, user_b=user_b,
        defaults={"connection_type": "match", "weight": 1},
    )

    Interaction.objects.create(actor=user_a, target=user_b, community=community, interaction_type="match")
    Interaction.objects.create(actor=user_b, target=user_a, community=community, interaction_type="match")

    return match


def assign_buddy(new_user, community):
    """
    Assign a buddy to a new member of a community.
    Criteria: active member + same interests + not overloaded.
    """
    from communities.models import Membership

    existing = BuddyAssignment.objects.filter(new_user=new_user, community=community).first()
    if existing:
        return existing

    members = (
        Membership.objects.filter(community=community)
        .exclude(user=new_user)
        .select_related("user", "user__profile")
    )

    try:
        new_profile = new_user.profile
        new_interests = set(new_profile.interests_list())
    except Exception:
        new_interests = set()

    best_buddy = None
    best_score = -1

    for membership in members:
        candidate = membership.user

        # Skip if already buddy-assigned too many (cap at 3)
        buddy_count = BuddyAssignment.objects.filter(buddy_user=candidate, community=community).count()
        if buddy_count >= 3:
            continue

        try:
            cand_interests = set(candidate.profile.interests_list())
        except Exception:
            cand_interests = set()

        shared = len(new_interests & cand_interests)
        if shared > best_score:
            best_score = shared
            best_buddy = candidate

    if best_buddy is None and members.exists():
        best_buddy = members.first().user

    if best_buddy:
        assignment = BuddyAssignment.objects.create(
            new_user=new_user, buddy_user=best_buddy, community=community
        )
        Connection.objects.get_or_create(
            user_a=best_buddy, user_b=new_user,
            defaults={"connection_type": "buddy", "weight": 1},
        )
        Interaction.objects.create(
            actor=best_buddy, target=new_user, community=community, interaction_type="introduction"
        )
        return assignment
    return None
