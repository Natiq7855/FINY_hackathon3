from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    skills = models.TextField(
        blank=True,
        help_text="Comma-separated list of skills, e.g. python,design,marketing",
    )
    interests = models.TextField(
        blank=True,
        help_text="Comma-separated list of interests",
    )
    goals = models.TextField(blank=True)
    timezone = models.CharField(max_length=64, blank=True, default="UTC")
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def skills_list(self):
        return [s.strip().lower() for s in self.skills.split(",") if s.strip()]

    def interests_list(self):
        return [i.strip().lower() for i in self.interests.split(",") if i.strip()]

    def __str__(self):
        return f"{self.user.username}'s profile"
