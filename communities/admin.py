from django.contrib import admin
from .models import Community, Membership


@admin.register(Community)
class CommunityAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "member_count", "created_at")
    search_fields = ("name",)


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "community", "role", "joined_at")
    list_filter = ("role", "community")
    search_fields = ("user__username", "community__name")
