from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsJournalist(BasePermission):
    """Allows access only to users with the Journalist role."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.role == 'journalist')


class IsEditorOrJournalist(BasePermission):
    """
    Allows write access to Editors and Journalists. Journalists may
    only modify their own articles; Editors may modify any article.
    Read access (safe methods) is allowed for any authenticated user.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.role in ('editor', 'journalist'))

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if request.user.role == 'editor':
            return True
        # Journalists can only modify their own articles.
        return obj.author_id == request.user.id