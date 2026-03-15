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


DEMO_USERS = [
    {"username": "alice", "first_name": "Alice", "last_name": "Chen",
     "skills": "python,django,data science", "interests": "open-source,music,hiking",
     "timezone": "UTC", "bio": "Full-stack developer passionate about data."},
    {"username": "bob", "first_name": "Bob", "last_name": "Martinez",
     "skills": "react,javascript,design", "interests": "open-source,travel,photography",
     "timezone": "UTC", "bio": "Frontend engineer who loves building beautiful UIs."},
    {"username": "carol", "first_name": "Carol", "last_name": "Davies",
     "skills": "marketing,content,seo", "interests": "writing,travel,music",
     "timezone": "UTC", "bio": "Community builder and content strategist."},
    {"username": "dave", "first_name": "Dave", "last_name": "Park",
     "skills": "python,machine learning,data science", "interests": "ai,hiking,gaming",
     "timezone": "UTC", "bio": "ML researcher working on NLP problems."},
    {"username": "eve", "first_name": "Eve", "last_name": "Wilson",
     "skills": "design,figma,ux", "interests": "art,photography,music",
     "timezone": "UTC", "bio": "UX designer focused on human-centered design."},
]

ADMIN_USER = {"username": "admin", "email": "admin@peerweave.dev", "password": "admin1234"}


class Command(BaseCommand):
    help = "Seed demo data (5 users, 1 community, matches, help requests)"

    def handle(self, *args, **options):
        self.stdout.write("Seeding demo data...")

        # Admin
        admin, _ = User.objects.get_or_create(username=ADMIN_USER["username"])
        admin.email = ADMIN_USER["email"]
        admin.set_password(ADMIN_USER["password"])
        admin.is_staff = True
        admin.is_superuser = True
        admin.save()
        self.stdout.write(f"  Admin: {admin.username} / {ADMIN_USER['password']}")

        # Demo community
        community, _ = Community.objects.get_or_create(
            name="PeerWeave Demo",
            defaults={"description": "The official demo community for PeerWeave.", "owner": admin},
        )
        Membership.objects.get_or_create(user=admin, community=community, defaults={"role": "admin"})

        # Demo users
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
            profile.save()

            Membership.objects.get_or_create(user=user, community=community)
            users.append(user)
            self.stdout.write(f"  User: {user.username} / demo1234")

        # Create some connections and matches
        alice, bob, carol, dave, eve = users
        pairs = [(alice, bob, "match"), (alice, dave, "match"), (bob, eve, "buddy"),
                 (carol, eve, "help"), (dave, carol, "match")]
        for u_a, u_b, ctype in pairs:
            Connection.objects.get_or_create(user_a=u_a, user_b=u_b, defaults={"connection_type": ctype})
            Match.objects.get_or_create(user_a=u_a, user_b=u_b, community=community,
                                        defaults={"status": "accepted"})
            Interaction.objects.get_or_create(
                actor=u_a, target=u_b, community=community,
                defaults={"interaction_type": "match"},
            )

        # Help requests
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

        self.stdout.write(self.style.SUCCESS("\nDemo data seeded successfully!"))
        self.stdout.write("\nLogin credentials:")
        self.stdout.write("  admin / admin1234  (superuser)")
        self.stdout.write("  alice / demo1234")
        self.stdout.write("  bob   / demo1234")
        self.stdout.write("  carol / demo1234")
        self.stdout.write("  dave  / demo1234")
        self.stdout.write("  eve   / demo1234")
