from django.db.models.signals import post_save
from django.dispatch import receiver
from matchmaking.models import Match, BuddyAssignment
from helpboard.models import HelpResponse
from .models import Badge, UserBadge


def _award(user, trigger_type):
    """Award a badge to a user if it exists and hasn't been awarded yet."""
    badge = Badge.objects.filter(trigger_type=trigger_type).first()
    if badge:
        UserBadge.objects.get_or_create(user=user, badge=badge)


@receiver(post_save, sender=HelpResponse)
def award_help_badge(sender, instance, created, **kwargs):
    if created:
        _award(instance.helper, "help_answer")


@receiver(post_save, sender=Match)
def award_match_badge(sender, instance, created, **kwargs):
    if created:
        _award(instance.user_a, "match_initiate")


@receiver(post_save, sender=BuddyAssignment)
def award_buddy_badge(sender, instance, created, **kwargs):
    if created:
        _award(instance.buddy_user, "buddy_mentor")
