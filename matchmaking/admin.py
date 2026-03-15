from django.contrib import admin
from .models import Match, BuddyAssignment, Connection, Interaction


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ("user_a", "user_b", "community", "status", "created_at")
    list_filter = ("status", "community")


@admin.register(BuddyAssignment)
class BuddyAssignmentAdmin(admin.ModelAdmin):
    list_display = ("new_user", "buddy_user", "community", "created_at")
    list_filter = ("community",)


@admin.register(Connection)
class ConnectionAdmin(admin.ModelAdmin):
    list_display = ("user_a", "user_b", "connection_type", "weight", "created_at")
    list_filter = ("connection_type",)


@admin.register(Interaction)
class InteractionAdmin(admin.ModelAdmin):
    list_display = ("actor", "target", "community", "interaction_type", "timestamp")
    list_filter = ("interaction_type", "community")
