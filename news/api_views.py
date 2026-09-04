from django.db.models import Q
from rest_framework import viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Article
from .serializers import ArticleSerializer
from .permissions import IsJournalist, IsEditorOrJournalist


class ArticleViewSet(viewsets.ModelViewSet):
    """
    RESTful endpoints for articles.

    - list / retrieve: any authenticated user (approved articles only
      for the list; a specific article can be retrieved directly).
    - create: Journalists only. The author is set automatically from
      the requesting user, never taken from client input.
    - update / destroy: Editors (any article) or the Journalist who
      wrote the article (their own only).
    """
    serializer_class = ArticleSerializer

    def get_queryset(self):
        if self.action == 'list':
            return Article.objects.filter(approved=True).order_by('-created_at')
        return Article.objects.all()

    def get_permissions(self):
        if self.action == 'create':
            return [IsJournalist()]
        if self.action in ('update', 'partial_update', 'destroy'):
            return [IsEditorOrJournalist()]
        return super().get_permissions()

    def perform_create(self, serializer):
        # Author is always the logged-in journalist, never client-supplied.
        serializer.save(author=self.request.user)

    @action(detail=False, methods=['get'])
    def subscribed(self, request):
        """
        Returns approved articles from publishers or journalists that
        the requesting reader is subscribed to.
        """
        user = request.user
        articles = Article.objects.filter(
            Q(publisher__in=user.subscriptions_to_publishers.all()) |
            Q(author__in=user.subscriptions_to_journalists.all()),
            approved=True
        ).distinct().order_by('-created_at')
        serializer = self.get_serializer(articles, many=True)
        return Response(serializer.data)


@api_view(['POST'])
@permission_classes([AllowAny])  # internal simulated call; tighten later if needed
def approved_article_log(request):
    """
    Receives the approved article data POSTed from the approval view and
    logs it. Simulates externally distributing the article while keeping
    the whole flow inside this project.
    """
    print("Approved article logged via /api/approved/:", request.data)
    return Response({'status': 'logged', 'article': request.data}, status=201)