"""
Management command to seed demo data for PeerWeave.
Run with: python manage.py seed_demo
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import Profile
from communities.models import Community, Membership
from matchmaking.models import Match, Connection, Interaction, BuddyAssignment
from helpboard.models import HelpRequest, HelpResponse
from squads.models import Squad
from agents.models import AgentAction
from badges.models import Badge, UserBadge


DEMO_USERS = [
    {"username": "alice", "first_name": "Alice", "last_name": "Chen",
     "skills": "python,django,data science", "interests": "open-source,music,hiking",
     "timezone": "UTC", "bio": "Full-stack developer passionate about data.",
     "intent": "build", "communication_style": "deep_analysis"},
    {"username": "bob", "first_name": "Bob", "last_name": "Martinez",
     "skills": "react,javascript,design", "interests": "open-source,travel,photography",
     "timezone": "UTC", "bio": "Frontend engineer who loves building beautiful UIs.",
     "intent": "collaborate", "communication_style": "fast_discussion"},
    {"username": "carol", "first_name": "Carol", "last_name": "Davies",
     "skills": "marketing,content,seo", "interests": "writing,travel,music",
     "timezone": "UTC", "bio": "Community builder and content strategist.",
     "intent": "explore", "communication_style": "casual_chat"},
    {"username": "dave", "first_name": "Dave", "last_name": "Park",
     "skills": "python,machine learning,data science", "interests": "ai,hiking,gaming",
     "timezone": "UTC", "bio": "ML researcher working on NLP problems.",
     "intent": "learn", "communication_style": "deep_analysis"},
    {"username": "eve", "first_name": "Eve", "last_name": "Wilson",
     "skills": "design,figma,ux", "interests": "art,photography,music",
     "timezone": "UTC", "bio": "UX designer focused on human-centered design.",
     "intent": "collaborate", "communication_style": "casual_chat"},
]

ADMIN_USER = {"username": "admin", "email": "admin@peerweave.dev", "password": "admin1234"}

BADGE_DEFINITIONS = [
    {"name": "Helper", "icon": "🤝", "trigger_type": "help_answer",
     "description": "Awarded for answering a help request."},
    {"name": "Connector", "icon": "🔗", "trigger_type": "match_initiate",
     "description": "Awarded for initiating a peer match."},
    {"name": "Reviver", "icon": "🔥", "trigger_type": "squad_revive",
     "description": "Awarded for helping revive an inactive squad."},
    {"name": "Pioneer", "icon": "🚀", "trigger_type": "first_connection",
     "description": "Awarded for making a first connection."},
    {"name": "Mentor", "icon": "🎓", "trigger_type": "buddy_mentor",
     "description": "Awarded for mentoring a new member as buddy."},
]


class Command(BaseCommand):
    help = "Seed demo data (users, community, squads, badges, agent actions)"

    def handle(self, *args, **options):
        self.stdout.write("Seeding demo data...")

        # ── Admin ────────────────────────────────────────────────────
        admin, _ = User.objects.get_or_create(username=ADMIN_USER["username"])
        admin.email = ADMIN_USER["email"]
        admin.set_password(ADMIN_USER["password"])
        admin.is_staff = True
        admin.is_superuser = True
        admin.save()
        self.stdout.write(f"  Admin: {admin.username} / {ADMIN_USER['password']}")

        # ── Community ────────────────────────────────────────────────
        community, _ = Community.objects.get_or_create(
            name="PeerWeave Demo",
            defaults={"description": "The official demo community for PeerWeave.", "owner": admin},
        )
        Membership.objects.get_or_create(user=admin, community=community, defaults={"role": "admin"})

        # ── Demo Users ───────────────────────────────────────────────
        users = []
        for data in DEMO_USERS:
            user, created = User.objects.get_or_create(username=data["username"])
            if created or not user.has_usable_password():
                user.set_password("demo1234")
            user.first_name = data["first_name"]
            user.last_name = data["last_name"]
            user.email = f"{data['username']}@example.com"
            user.save()

            profile = user.profile
            profile.skills = data["skills"]
            profile.interests = data["interests"]
            profile.timezone = data["timezone"]
            profile.bio = data["bio"]
            profile.intent = data["intent"]
            profile.communication_style = data["communication_style"]
            profile.onboarding_complete = True
            profile.save()

            Membership.objects.get_or_create(user=user, community=community)
            users.append(user)
            self.stdout.write(f"  User: {user.username} / demo1234")

        # ── Connections & Matches ────────────────────────────────────
        alice, bob, carol, dave, eve = users
        pairs = [
            (alice, bob, "match"), (alice, dave, "match"), (bob, eve, "buddy"),
            (carol, eve, "help"), (dave, carol, "match"),
        ]
        for u_a, u_b, ctype in pairs:
            Connection.objects.get_or_create(user_a=u_a, user_b=u_b, defaults={"connection_type": ctype})
            Match.objects.get_or_create(
                user_a=u_a, user_b=u_b, community=community,
                defaults={"status": "accepted"},
            )
            Interaction.objects.get_or_create(
                actor=u_a, target=u_b, community=community,
                defaults={"interaction_type": "match"},
            )

        # ── Help Requests ────────────────────────────────────────────
        reqs = [
            {"author": carol, "title": "How do I set up Django REST Framework?",
             "description": "I'm new to Django and need help setting up DRF for an API project.",
             "tags": "python,django,api", "status": "open"},
            {"author": bob, "title": "Best UX patterns for dashboards?",
             "description": "Looking for advice on dashboard layout and data visualization.",
             "tags": "design,ux,figma", "status": "open"},
            {"author": dave, "title": "Marketing strategy for open-source project",
             "description": "Need help thinking through a go-to-market plan for an OSS tool.",
             "tags": "marketing,content", "status": "solved"},
        ]
        for rdata in reqs:
            req, created = HelpRequest.objects.get_or_create(
                title=rdata["title"],
                defaults={
                    "author": rdata["author"], "community": community,
                    "description": rdata["description"], "tags": rdata["tags"],
                    "status": rdata["status"],
                },
            )
            if created and rdata["status"] == "solved":
                HelpResponse.objects.get_or_create(
                    request=req, helper=carol,
                    defaults={"message": "Here is a comprehensive answer to your question!"},
                )

        # ── Badges ───────────────────────────────────────────────────
        self.stdout.write("\n  Seeding badges...")
        for bdata in BADGE_DEFINITIONS:
            badge, created = Badge.objects.get_or_create(
                trigger_type=bdata["trigger_type"],
                defaults={
                    "name": bdata["name"],
                    "icon": bdata["icon"],
                    "description": bdata["description"],
                },
            )
            if created:
                self.stdout.write(f"    Badge: {badge.name}")

        # Award some demo badges
        helper_badge = Badge.objects.filter(trigger_type="help_answer").first()
        connector_badge = Badge.objects.filter(trigger_type="match_initiate").first()
        mentor_badge = Badge.objects.filter(trigger_type="buddy_mentor").first()
        pioneer_badge = Badge.objects.filter(trigger_type="first_connection").first()

        if helper_badge:
            UserBadge.objects.get_or_create(user=carol, badge=helper_badge)
        if connector_badge:
            UserBadge.objects.get_or_create(user=alice, badge=connector_badge)
            UserBadge.objects.get_or_create(user=dave, badge=connector_badge)
        if mentor_badge:
            UserBadge.objects.get_or_create(user=bob, badge=mentor_badge)
        if pioneer_badge:
            for u in users:
                UserBadge.objects.get_or_create(user=u, badge=pioneer_badge)

        # ── Squads ───────────────────────────────────────────────────
        self.stdout.write("\n  Seeding squads...")

        squad1, created = Squad.objects.get_or_create(
            community=community, name="Data & Python",
            defaults={"topic_focus": ["python", "data science", "ai"], "health_score": 85},
        )
        if created:
            squad1.members.set([alice, dave])
            self.stdout.write(f"    Squad: {squad1.name} (alice, dave)")

        squad2, created = Squad.objects.get_or_create(
            community=community, name="Design & Creative",
            defaults={"topic_focus": ["design", "photography", "music"], "health_score": 60},
        )
        if created:
            squad2.members.set([bob, eve, carol])
            self.stdout.write(f"    Squad: {squad2.name} (bob, eve, carol)")

        # ── Agent Actions ────────────────────────────────────────────
        self.stdout.write("\n  Seeding Shadow Founder actions...")
        AgentAction.objects.get_or_create(
            squad=squad2, action_type="conversation_starter",
            defaults={
                "payload": {
                    "message": "What's a design tool or technique you recently discovered that changed your workflow?",
                    "context": "demo_seed",
                    "topic_focus": squad2.topic_focus,
                    "member_count": squad2.member_count(),
                    "idle_hours": 24,
                },
                "status": "executed",
            },
        )
        AgentAction.objects.get_or_create(
            squad=squad1, action_type="activity_prompt",
            defaults={
                "payload": {
                    "message": "Quick challenge: share one Python trick you learned this week!",
                    "context": "demo_seed",
                    "topic_focus": squad1.topic_focus,
                    "member_count": squad1.member_count(),
                    "idle_hours": 36,
                },
                "status": "executed",
            },
        )

        # ── Done ─────────────────────────────────────────────────────
        self.stdout.write(self.style.SUCCESS("\nDemo data seeded successfully!"))
        self.stdout.write("\nLogin credentials:")
        self.stdout.write("  admin / admin1234  (superuser)")
        self.stdout.write("  alice / demo1234   (build, deep analysis)")
        self.stdout.write("  bob   / demo1234   (collaborate, fast discussion)")
        self.stdout.write("  carol / demo1234   (explore, casual chat)")
        self.stdout.write("  dave  / demo1234   (learn, deep analysis)")
        self.stdout.write("  eve   / demo1234   (collaborate, casual chat)")
