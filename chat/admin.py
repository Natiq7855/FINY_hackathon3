from django.contrib import admin
from .models import Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("sender", "community", "content_preview", "created_at")
    list_filter = ("community",)
    search_fields = ("sender__username", "content")

    def content_preview(self, obj):
        return obj.content[:60]
    content_preview.short_description = "Content"
