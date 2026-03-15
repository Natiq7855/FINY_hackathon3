from django.db.models import Q
from .models import Match, Connection, Interaction, BuddyAssignment


# ── Compatibility Scoring Engine ─────────────────────────────────────

def compute_compatibility_score(user, candidate) -> float:
    """
    Enhanced compatibility score for squad placement and matching.
    score = 0.5 * interest_overlap + 0.3 * intent_match + 0.2 * comm_style
    Returns a float between 0.0 and 1.0.
    """
    try:
        p1 = user.profile
        p2 = candidate.profile
    except Exception:
        return 0.0

    # Interest overlap (Jaccard)
    i1 = set(p1.interests_list())
    i2 = set(p2.interests_list())
    if i1 or i2:
        interest_overlap = len(i1 & i2) / len(i1 | i2) if (i1 | i2) else 0.0
    else:
        interest_overlap = 0.0

    # Intent match (binary)
    intent_match = 1.0 if (p1.intent and p1.intent == p2.intent) else 0.0

    # Communication style (binary)
    comm_match = 1.0 if (p1.communication_style and p1.communication_style == p2.communication_style) else 0.0

    return 0.5 * interest_overlap + 0.3 * intent_match + 0.2 * comm_match


SQUAD_COMPATIBILITY_THRESHOLD = 0.35


def place_in_squad(user, community):
    """
    Try to place user into existing squad with highest compatibility.
    If no squad score > threshold, create a new squad.
    Returns the Squad the user was placed in.
    """
    from squads.models import Squad

    active_squads = Squad.objects.filter(community=community, is_active=True)
    best_squad = None
    best_avg_score = -1.0

    for squad in active_squads:
        if squad.is_full():
            continue
        members = squad.members.all()
        if not members:
            continue
        total = sum(compute_compatibility_score(user, m) for m in members)
        avg = total / members.count()
        if avg > best_avg_score:
            best_avg_score = avg
            best_squad = squad

    if best_squad and best_avg_score >= SQUAD_COMPATIBILITY_THRESHOLD:
        best_squad.add_member(user)
        return best_squad

    # No compatible squad — create new one
    try:
        interests = user.profile.interests_list()[:3]
    except Exception:
        interests = []
    name = " & ".join(t.title() for t in interests) if interests else f"{user.username}'s Squad"
    new_squad = Squad.objects.create(
        community=community,
        name=name,
        topic_focus=interests,
    )
    new_squad.members.add(user)
    return new_squad


# ── Original Match Scoring (kept for backwards compat) ───────────────

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
