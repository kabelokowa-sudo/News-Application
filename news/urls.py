"""
URL routes for the news app: front-end pages (home, register, login,
logout, editor workflow) plus the DRF API endpoints.
"""
from django.contrib.auth import views as auth_views
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views
from . import api_views

router = DefaultRouter()
router.register(r'api/articles', api_views.ArticleViewSet, basename='article')

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='news/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('editor/pending/', views.pending_articles, name='pending_articles'),
    path('editor/approve/<int:article_id>/', views.approve_article, name='approve_article'),
    path('api/approved/', api_views.approved_article_log, name='approved_article_log'),
    path('', include(router.urls)),
]
