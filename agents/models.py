from django.db import models


class AgentAction(models.Model):
    ACTION_TYPES = [
        ("conversation_starter", "Conversation Starter"),
        ("activity_prompt", "Activity Prompt"),
        ("member_highlight", "Member Highlight"),
        ("challenge_post", "Challenge Post"),
    ]
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("executed", "Executed"),
        ("failed", "Failed"),
    ]

    squad = models.ForeignKey(
        "squads.Squad", on_delete=models.CASCADE, related_name="agent_actions"
    )
    action_type = models.CharField(max_length=32, choices=ACTION_TYPES)
    payload = models.JSONField(default=dict)
    executed_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="pending")

    class Meta:
        ordering = ["-executed_at"]

    def __str__(self):
        return f"{self.action_type} → {self.squad.name} ({self.status})"
