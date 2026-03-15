from django.db.models.signals import post_save
from django.dispatch import receiver
from communities.models import Membership


@receiver(post_save, sender=Membership)
def on_membership_created(sender, instance, created, **kwargs):
    if created:
        from .services import assign_buddy
        assign_buddy(instance.user, instance.community)
