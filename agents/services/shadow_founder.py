"""
Shadow Founder AI — monitors squad activity and intervenes
when engagement drops, generating AI-powered conversation starters.
"""
import json
import logging
from datetime import timedelta

from django.utils import timezone

from agents.models import AgentAction
from squads.models import Squad
from matchmaking.models import Interaction

logger = logging.getLogger(__name__)


def _generate_starter(topic_focus: list[str]) -> dict:
    """
    Generate a conversation starter using Gemini AI.
    Falls back to a template-based starter if AI is unavailable.
    """
    topics_str = ", ".join(topic_focus) if topic_focus else "general topics"

    try:
        from google import genai
        from django.conf import settings

        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        prompt = (
            f"Generate a short, engaging conversation starter question for a small "
            f"online community group focused on: {topics_str}. "
            f"Return JSON: {{\"message\": \"...\", \"context\": \"...\"}}"
        )
        response = client.models.generate_content(
            model="gemini-2.0-flash", contents=prompt
        )
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text)
    except Exception as exc:
        logger.warning("Gemini starter generation failed: %s", exc)
        return {
            "message": f"What's everyone working on this week related to {topics_str}?",
            "context": "auto_fallback",
        }


def check_and_intervene() -> list[AgentAction]:
    """
    Scan all active squads. If a squad has zero interactions in the
    last 24 hours, generate a conversation starter and log an AgentAction.
    Returns list of actions taken.
    """
    cutoff = timezone.now() - timedelta(hours=24)
    active_squads = Squad.objects.filter(is_active=True).select_related("community")
    actions_taken = []

    for squad in active_squads:
        member_ids = list(squad.members.values_list("id", flat=True))
        if len(member_ids) < 2:
            continue

        recent_interactions = Interaction.objects.filter(
            community=squad.community,
            actor_id__in=member_ids,
            target_id__in=member_ids,
            timestamp__gte=cutoff,
        ).count()

        if recent_interactions == 0:
            # Squad is idle — intervene
            starter = _generate_starter(squad.topic_focus)
            action = AgentAction.objects.create(
                squad=squad,
                action_type="conversation_starter",
                payload={
                    "message": starter.get("message", ""),
                    "context": starter.get("context", ""),
                    "topic_focus": squad.topic_focus,
                    "member_count": len(member_ids),
                    "idle_hours": 24,
                },
                status="executed",
            )
            # Decrease squad health for inactivity
            squad.health_score = max(0, squad.health_score - 10)
            squad.save(update_fields=["health_score"])

            actions_taken.append(action)
            logger.info("Shadow Founder intervened in squad %s", squad.name)

    return actions_taken
