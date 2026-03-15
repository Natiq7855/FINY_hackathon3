from django.contrib import admin
from .models import AgentAction


@admin.register(AgentAction)
class AgentActionAdmin(admin.ModelAdmin):
    list_display = ("squad", "action_type", "status", "executed_at")
    list_filter = ("action_type", "status")
    readonly_fields = ("payload",)
