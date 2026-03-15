from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.utils.html import escape
from communities.models import Community, Membership
from matchmaking.models import Connection, Interaction
from .models import Message, CHANNEL_CHOICES

VALID_CHANNELS = {slug for slug, _ in CHANNEL_CHOICES}

CHANNEL_META = {
    "general": {
        "label": "general",
        "topic": "Community general chat — say hello and connect with members 👋",
    },
    "help": {
        "label": "help",
        "topic": "Ask questions and share expertise — tag your message with a skill to get noticed 🙋",
    },
}


def _require_membership(user, community):
    return Membership.objects.filter(user=user, community=community).exists()


@login_required
def chat_room(request, community_id, channel="general"):
    if channel not in VALID_CHANNELS:
        channel = "general"

    community = get_object_or_404(Community, pk=community_id)
    if not _require_membership(request.user, community):
        return HttpResponseForbidden("You are not a member of this community.")

    members = community.memberships.select_related("user", "user__profile").order_by("user__username")

    # Last 50 messages for this channel
    messages_qs = (
        Message.objects.filter(community=community, channel=channel)
        .select_related("sender")
        .order_by("-created_at")[:50]
    )
    initial_messages = list(reversed(messages_qs))

    # Unread counts: messages in OTHER channels (simple: latest id per channel)
    unread_counts = {}
    for slug, _ in CHANNEL_CHOICES:
        if slug != channel:
            unread_counts[slug] = Message.objects.filter(community=community, channel=slug).count()

    # All communities the user belongs to — for the server sidebar
    user_communities = (
        Membership.objects.filter(user=request.user)
        .select_related("community")
        .order_by("community__name")
    )

    return render(request, "chat/room.html", {
        "community": community,
        "channel": channel,
        "channel_meta": CHANNEL_META.get(channel, {"label": channel, "topic": ""}),
        "channels": CHANNEL_CHOICES,
        "unread_counts": unread_counts,
        "members": members,
        "initial_messages": initial_messages,
        "user_communities": user_communities,
    })


@login_required
def messages_api(request, community_id, channel="general"):
    if channel not in VALID_CHANNELS:
        return HttpResponseBadRequest("Invalid channel")

    community = get_object_or_404(Community, pk=community_id)
    if not _require_membership(request.user, community):
        return JsonResponse({"error": "Forbidden"}, status=403)

    after_id = request.GET.get("after", 0)
    try:
        after_id = int(after_id)
    except (ValueError, TypeError):
        after_id = 0

    qs = (
        Message.objects.filter(community=community, channel=channel, id__gt=after_id)
        .select_related("sender")
        .order_by("created_at")
    )

    data = [
        {
            "id": m.id,
            "sender": m.sender.username,
            "sender_display": m.sender.get_full_name() or m.sender.username,
            "is_me": m.sender_id == request.user.id,
            "content": escape(m.content),
            "time": m.created_at.strftime("%H:%M"),
            "date": m.created_at.strftime("%b %d"),
        }
        for m in qs
    ]
    return JsonResponse({"messages": data})


@login_required
@require_POST
def send_message(request, community_id, channel="general"):
    if channel not in VALID_CHANNELS:
        return JsonResponse({"error": "Invalid channel"}, status=400)

    community = get_object_or_404(Community, pk=community_id)
    if not _require_membership(request.user, community):
        return JsonResponse({"error": "Forbidden"}, status=403)

    content = request.POST.get("content", "").strip()
    if not content:
        return JsonResponse({"error": "Empty message"}, status=400)
    if len(content) > 2000:
        return JsonResponse({"error": "Message too long (max 2000 chars)"}, status=400)

    msg = Message.objects.create(
        community=community, sender=request.user, channel=channel, content=content
    )

    # Log interaction for health score / graph
    member_ids = list(
        Membership.objects.filter(community=community)
        .exclude(user=request.user)
        .values_list("user_id", flat=True)[:1]
    )
    if member_ids:
        from django.contrib.auth.models import User as UserModel
        other = UserModel.objects.get(pk=member_ids[0])
        Connection.objects.get_or_create(
            user_a=request.user, user_b=other,
            defaults={"connection_type": "chat", "weight": 1},
        )
        Interaction.objects.create(
            actor=request.user, target=other,
            community=community, interaction_type="message",
        )

    return JsonResponse({
        "id": msg.id,
        "sender": msg.sender.username,
        "sender_display": msg.sender.get_full_name() or msg.sender.username,
        "is_me": True,
        "content": escape(msg.content),
        "time": msg.created_at.strftime("%H:%M"),
        "date": msg.created_at.strftime("%b %d"),
    })

