from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import CustomUser


@receiver(post_save, sender=CustomUser)
def sync_user_role(sender, instance, created, **kwargs):
    """
    This runs every time a user is saved (created or edited).

    It does two things based on the user's role:
    1. Puts them in the matching Group (Reader, Editor, or Journalist)
       so they get the right permissions.
    2. If they're a Journalist, clears their subscription fields,
       since subscriptions are only meant for Readers.

    We can't clear the Reader's "articles written" the same way,
    because Article.author is a required field - clearing it would
    mean deleting their articles, which we don't want to do.
    """
    # Step 1: fix the user's group.
    # Take them out of all 3 role groups first, then add the correct one.
    role_group_names = ['Reader', 'Editor', 'Journalist']
    instance.groups.remove(*Group.objects.filter(name__in=role_group_names))

    correct_group_name = instance.role.capitalize()  # e.g. 'editor' -> 'Editor'
    correct_group, _ = Group.objects.get_or_create(name=correct_group_name)
    instance.groups.add(correct_group)

    # Step 2: clear subscription fields if this user is now a Journalist.
    if instance.role == CustomUser.Role.JOURNALIST:
        instance.subscriptions_to_publishers.clear()
        instance.subscriptions_to_journalists.clear()