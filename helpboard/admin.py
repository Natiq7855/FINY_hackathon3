from django.contrib import admin
from .models import HelpRequest, HelpResponse


@admin.register(HelpRequest)
class HelpRequestAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "community", "status", "created_at")
    list_filter = ("status", "community")
    search_fields = ("title", "description", "tags")


@admin.register(HelpResponse)
class HelpResponseAdmin(admin.ModelAdmin):
    list_display = ("helper", "request", "created_at")
