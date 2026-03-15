from django.db import models
from django.contrib.auth.models import User
from communities.models import Community


CHANNEL_CHOICES = [
    ("general", "# general"),
    ("help",    "# help"),
]

class Message(models.Model):
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages")
    channel = models.CharField(max_length=32, choices=CHANNEL_CHOICES, default="general", db_index=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"[{self.channel}] {self.sender.username}: {self.content[:40]}"
