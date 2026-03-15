from django.db import models
from django.contrib.auth.models import User


class Badge(models.Model):
    TRIGGER_TYPES = [
        ("help_answer", "Answered a Help Request"),
        ("match_initiate", "Initiated a Match"),
        ("squad_revive", "Revived Inactive Squad"),
        ("first_connection", "First Connection Made"),
        ("buddy_mentor", "Buddy Mentored a New Member"),
    ]

    name = models.CharField(max_length=64, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=8, default="🏅")
    trigger_type = models.CharField(max_length=32, choices=TRIGGER_TYPES, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.icon} {self.name}"


class UserBadge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="badges")
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name="awards")
    awarded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "badge")
        ordering = ["-awarded_at"]

    def __str__(self):
        return f"{self.user.username} → {self.badge.name}"
