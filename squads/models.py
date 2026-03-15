from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from communities.models import Community


class Squad(models.Model):
    community = models.ForeignKey(
        Community, on_delete=models.CASCADE, related_name="squads"
    )
    name = models.CharField(max_length=128)
    members = models.ManyToManyField(User, related_name="squads", blank=True)
    topic_focus = models.JSONField(default=list, blank=True)
    health_score = models.IntegerField(default=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    MAX_MEMBERS = 12

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.community.name})"

    def member_count(self):
        return self.members.count()

    def is_full(self):
        return self.member_count() >= self.MAX_MEMBERS

    def add_member(self, user):
        if self.members.count() >= self.MAX_MEMBERS:
            raise ValidationError("A squad cannot exceed 12 members.")
        self.members.add(user)

    def clean(self):
        super().clean()
        if self.pk and self.members.count() > self.MAX_MEMBERS:
            raise ValidationError("A squad cannot exceed 12 members.")
