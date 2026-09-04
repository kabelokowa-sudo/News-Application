from rest_framework import serializers

from .models import Article, Publisher, Newsletter, CustomUser


class ArticleSerializer(serializers.ModelSerializer):
    """Serializes Article data for the REST API and the /api/approved/ log."""

    author = serializers.StringRelatedField()
    publisher = serializers.StringRelatedField()

    class Meta:
        model = Article
        fields = ['id', 'title', 'content', 'author', 'publisher', 'created_at', 'approved']


class PublisherSerializer(serializers.ModelSerializer):
    """Serializes Publisher data (id and name) for the REST API."""

    class Meta:
        model = Publisher
        fields = ['id', 'name']


class NewsletterSerializer(serializers.ModelSerializer):
    """Serializes Newsletter data, including its collection of articles."""

    class Meta:
        model = Newsletter
        fields = ['id', 'title', 'description', 'author', 'articles', 'created_at']


class UserSerializer(serializers.ModelSerializer):
    """Serializes basic CustomUser data (id, username, email, role)."""

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'role']
