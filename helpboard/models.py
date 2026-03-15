from django.db import models
from django.contrib.auth.models import User
from communities.models import Community


class HelpRequest(models.Model):
    STATUS_CHOICES = [("open", "Open"), ("solved", "Solved")]

    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="help_requests")
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name="help_requests")
    title = models.CharField(max_length=256)
    description = models.TextField()
    tags = models.TextField(
        blank=True, help_text="Comma-separated tags, e.g. python,design"
    )
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="open")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def tags_list(self):
        return [t.strip().lower() for t in self.tags.split(",") if t.strip()]

    def __str__(self):
        return self.title


class HelpResponse(models.Model):
    request = models.ForeignKey(HelpRequest, on_delete=models.CASCADE, related_name="responses")
    helper = models.ForeignKey(User, on_delete=models.CASCADE, related_name="help_responses")
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Response by {self.helper.username} on '{self.request.title}'"
