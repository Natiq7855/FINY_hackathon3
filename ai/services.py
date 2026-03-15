"""
Gemini AI service layer for PeerWeave.

Three main features:
  1. explain_peer_match    – why two users are a good match + ice-breaker question
  2. analyze_members       – per-member challenge detection + peer recommendation
  3. community_insights    – health score interpretation + action plan
"""
import json
import logging

from google import genai
from django.conf import settings

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _client


def _safe_generate(prompt: str, fallback) -> dict:
    """Call Gemini, parse JSON response, return fallback on any error."""
    try:
        response = _get_client().models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        text = response.text.strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text)
    except Exception as exc:
        logger.warning("Gemini call failed: %s", exc)
        return fallback


# ── 1. Peer Match Explainer ──────────────────────────────────────────────

def explain_peer_match(user_a, user_b) -> dict:
    """
    Returns:
        {
          "summary": "Why these two are a great match",
          "collaboration": "What they could work on together",
          "ice_breaker": "A specific first question user_a can ask user_b"
        }
    """
    def profile_text(u):
        try:
            p = u.profile
            return (
                f"Name: {u.get_full_name() or u.username}\n"
                f"Skills: {p.skills or 'not specified'}\n"
                f"Interests: {p.interests or 'not specified'}\n"
                f"Goals: {p.goals or 'not specified'}\n"
                f"Bio: {p.bio or 'not specified'}"
            )
        except Exception:
            return f"Name: {u.username}"

    prompt = f"""You are PeerWeave's AI matchmaker. Two community members have been matched.
Analyze their profiles and provide a match explanation.

--- Member A ---
{profile_text(user_a)}

--- Member B ---
{profile_text(user_b)}

Respond ONLY with valid JSON (no markdown, no extra text):
{{
  "summary": "2–3 sentence explanation of why they complement each other",
  "collaboration": "One specific project or activity they could work on together",
  "ice_breaker": "A single concrete question Member A can send Member B right now to start a conversation"
}}"""

    return _safe_generate(prompt, {
        "summary": "These two members share complementary skills and interests.",
        "collaboration": "Consider collaborating on a project that combines your strengths.",
        "ice_breaker": f"Hey {user_b.username}, I noticed we have some overlapping interests — would you be up for a quick chat?",
    })


# ── 2. Member Challenge & Peer Recommendation Analyzer ──────────────────

def analyze_members(community) -> list:
    """
    Analyzes every member of the community.
    Returns a list of dicts, one per member:
        {
          "username": str,
          "challenge": str,          # likely problem or gap
          "recommended_peer": str,   # username of best peer
          "reason": str,             # why that peer
          "question": str            # a question to spark connection
        }
    """
    memberships = community.memberships.select_related("user", "user__profile")

    if memberships.count() < 2:
        return []

    members_summary = []
    for m in memberships:
        u = m.user
        try:
            p = u.profile
            line = (
                f"username={u.username}, "
                f"skills=[{p.skills}], "
                f"interests=[{p.interests}], "
                f"goals={p.goals or 'none'}, "
                f"bio={p.bio or 'none'}"
            )
        except Exception:
            line = f"username={u.username}"
        members_summary.append(line)

    members_text = "\n".join(f"- {s}" for s in members_summary)

    prompt = f"""You are an AI community analyst for PeerWeave, a peer-matching platform.
Analyze the members of the "{community.name}" community.

Members:
{members_text}

For EACH member, identify:
1. A specific challenge or knowledge gap they are likely facing based on their profile
2. The single best peer from the other members they should connect with (by username)
3. Why that peer is the best recommendation
4. A warm, specific opening question the member could send to start a conversation

Respond ONLY with valid JSON array (no markdown fences, no extra text):
[
  {{
    "username": "...",
    "challenge": "One sentence describing a likely challenge or growth area",
    "recommended_peer": "username of best matching peer",
    "reason": "One sentence why this peer is ideal",
    "question": "A specific, friendly opening question they can send right now"
  }}
]"""

    result = _safe_generate(prompt, [])
    if not isinstance(result, list):
        return []
    return result


# ── 3. Community Health Insights ─────────────────────────────────────────

def community_insights(community, health_score: float) -> dict:
    """
    Returns:
        {
          "assessment": "2-sentence health summary",
          "strengths": ["...", "..."],
          "actions": [
            {"priority": "high|medium|low", "action": "...", "impact": "..."}
          ],
          "urgent": "urgent action string or null"
        }
    """
    from matchmaking.models import Connection, Interaction
    from helpboard.models import HelpRequest
    from django.utils import timezone
    from datetime import timedelta

    week_ago = timezone.now() - timedelta(days=7)
    member_ids = list(community.memberships.values_list("user_id", flat=True))
    member_count = len(member_ids)

    connections = Connection.objects.filter(
        user_a_id__in=member_ids, user_b_id__in=member_ids
    ).count()

    active = (
        Interaction.objects.filter(community=community, timestamp__gte=week_ago)
        .values("actor").distinct().count()
    )

    total_help = HelpRequest.objects.filter(community=community).count()
    solved_help = HelpRequest.objects.filter(community=community, status="solved").count()

    connected_ids = set(
        Connection.objects.filter(user_a_id__in=member_ids).values_list("user_a_id", flat=True)
    ) | set(
        Connection.objects.filter(user_b_id__in=member_ids).values_list("user_b_id", flat=True)
    )
    isolated = member_count - len(connected_ids.intersection(set(member_ids)))

    prompt = f"""You are a community health expert for PeerWeave.

Community: "{community.name}"
Description: {community.description or 'none'}
Health Score: {health_score}/100

Metrics (last 7 days):
- Total members: {member_count}
- Active members: {active}
- Total connections formed: {connections}
- Help questions: {total_help} total, {solved_help} solved
- Isolated members (zero connections): {isolated}

Provide a concise health analysis. Respond ONLY with valid JSON:
{{
  "assessment": "2 sentences describing the community health state",
  "strengths": ["up to 2 things the community does well"],
  "actions": [
    {{"priority": "high", "action": "specific action to take", "impact": "expected outcome"}},
    {{"priority": "medium", "action": "...", "impact": "..."}},
    {{"priority": "low", "action": "...", "impact": "..."}}
  ],
  "urgent": "one urgent action string if health < 40 or isolated > 30% of members, otherwise null"
}}"""

    return _safe_generate(prompt, {
        "assessment": f"{community.name} has a health score of {health_score}/100.",
        "strengths": ["Members are active", "Connections are forming"],
        "actions": [
            {"priority": "high", "action": "Encourage isolated members to introduce themselves", "impact": "Improves connectivity"},
            {"priority": "medium", "action": "Run a weekly matchmaking session", "impact": "Increases peer connections"},
            {"priority": "low", "action": "Share community achievements in #general", "impact": "Boosts morale"},
        ],
        "urgent": None,
    })
