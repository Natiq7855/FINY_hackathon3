from django.db import models
from django.contrib.auth.models import User
from communities.models import Community


class Match(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
    ]

    user_a = models.ForeignKey(User, on_delete=models.CASCADE, related_name="matches_as_a")
    user_b = models.ForeignKey(User, on_delete=models.CASCADE, related_name="matches_as_b")
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name="matches")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user_a.username} ↔ {self.user_b.username} ({self.community.name})"

    def other_user(self, user):
        return self.user_b if self.user_a == user else self.user_a


class BuddyAssignment(models.Model):
    new_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="buddy_assignments_new")
    buddy_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="buddy_assignments_buddy")
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name="buddy_assignments")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.buddy_user.username} buddy → {self.new_user.username}"


class Connection(models.Model):
    CONNECTION_TYPES = [
        ("match", "Match"),
        ("buddy", "Buddy"),
        ("help", "Help"),
        ("chat", "Chat"),
    ]

    user_a = models.ForeignKey(User, on_delete=models.CASCADE, related_name="connections_as_a")
    user_b = models.ForeignKey(User, on_delete=models.CASCADE, related_name="connections_as_b")
    connection_type = models.CharField(max_length=16, choices=CONNECTION_TYPES)
    weight = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user_a.username} — {self.user_b.username} ({self.connection_type})"


class Interaction(models.Model):
    INTERACTION_TYPES = [
        ("match", "Match"),
        ("help", "Help"),
        ("message", "Message"),
        ("introduction", "Introduction"),
    ]

    actor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="interactions_as_actor")
    target = models.ForeignKey(User, on_delete=models.CASCADE, related_name="interactions_as_target")
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name="interactions")
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.actor.username} → {self.target.username} ({self.interaction_type})"
