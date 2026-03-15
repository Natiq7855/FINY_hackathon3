from django.db import models
from django.contrib.auth.models import User


class Community(models.Model):
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="owned_communities")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "communities"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def member_count(self):
        return self.memberships.count()


class Membership(models.Model):
    ROLE_CHOICES = [("member", "Member"), ("admin", "Admin")]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="memberships")
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=16, choices=ROLE_CHOICES, default="member")
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "community")
        ordering = ["joined_at"]

    def __str__(self):
        return f"{self.user.username} in {self.community.name}"
