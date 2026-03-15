from django.contrib import admin
from .models import Squad


@admin.register(Squad)
class SquadAdmin(admin.ModelAdmin):
    list_display = ("name", "community", "member_count", "health_score", "is_active", "created_at")
    list_filter = ("is_active", "community")
    filter_horizontal = ("members",)
