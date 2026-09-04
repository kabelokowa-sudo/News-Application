from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """
    Custom user model with a role field controlling which features
    the user can access (Reader, Editor, or Journalist).

    Reader-specific fields (subscriptions) and Journalist-specific
    fields (published content) both live here. A signal (set up in
    signals.py) clears the fields that don't apply to the user's
    current role whenever a user is saved.
    """

    class Role(models.TextChoices):
        READER = 'reader', 'Reader'
        EDITOR = 'editor', 'Editor'
        JOURNALIST = 'journalist', 'Journalist'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.READER,
        help_text="Determines which group and permissions this user is given."
    )

    # Reader-only fields: what this user is subscribed to.
    subscriptions_to_publishers = models.ManyToManyField(
        'Publisher',
        blank=True,
        related_name='subscribed_readers'
    )
    subscriptions_to_journalists = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        related_name='subscribed_by_readers'
    )

    def __str__(self):
        return f"{self.username} ({self.role})"


class Publisher(models.Model):
    """
    A curated publication. A publisher has its own editors and
    journalists, who may also publish independently outside of
    the publisher (see Article.publisher, which is nullable).
    """

    name = models.CharField(max_length=200, unique=True)
    editors = models.ManyToManyField(
        CustomUser,
        blank=True,
        related_name='editor_at_publishers'
    )
    journalists = models.ManyToManyField(
        CustomUser,
        blank=True,
        related_name='journalist_at_publishers'
    )

    def __str__(self):
        return self.name


class Article(models.Model):
    """
    A news article written by a journalist. If `publisher` is set,
    the article is published content for that publisher; if it is
    left blank, the article is an independent piece by the author.
    """

    title = models.CharField(max_length=255)
    content = models.TextField()
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='articles'
    )
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='articles'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(
        default=False,
        help_text="Set to True by an editor to approve this article for publishing."
    )

    def __str__(self):
        return self.title


class Newsletter(models.Model):
    """
    A curated collection of articles, created by a journalist or
    editor. Readers can view newsletters; only journalists and
    editors can create or edit them.
    """

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='newsletters'
    )
    articles = models.ManyToManyField(Article, blank=True, related_name='newsletters')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title