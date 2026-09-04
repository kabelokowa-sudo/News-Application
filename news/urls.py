"""URL routes for the news app.

Combines the traditional Django views (editor pending/approve pages)
with the DRF router for the article API. Included at the root path by
:mod:`newsproject.urls`.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views
from . import api_views

router = DefaultRouter()
router.register(r'api/articles', api_views.ArticleViewSet, basename='article')

urlpatterns = [
    path('editor/pending/', views.pending_articles, name='pending_articles'),
    path('editor/approve/<int:article_id>/', views.approve_article, name='approve_article'),
    path('api/approved/', api_views.approved_article_log, name='approved_article_log'),
    path('', include(router.urls)),
]
