import requests
from django.contrib.auth.decorators import login_required, permission_required
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render

from .models import Article
from .serializers import ArticleSerializer


@login_required
@permission_required('news.change_article', raise_exception=True)
def pending_articles(request):
    """
    Shows editors a list of articles awaiting approval.
    Requires the 'change_article' permission (Editor or Journalist group).
    """
    articles = Article.objects.filter(approved=False).order_by('-created_at')
    return render(request, 'news/pending_articles.html', {'articles': articles})


@login_required
@permission_required('news.change_article', raise_exception=True)
def approve_article(request, article_id):
    """
    Approves an article, then:
    1. Emails the approved article to subscribers of its author/publisher.
    2. Logs the approved article to our own /api/approved/ endpoint via POST,
       simulating sharing it externally.
    """
    article = get_object_or_404(Article, id=article_id)
    article.approved = True
    article.save()

    # 1. Email subscribers of the journalist and/or publisher.
    subscriber_emails = set()
    subscriber_emails.update(
        article.author.subscribed_by_readers.values_list('email', flat=True)
    )
    if article.publisher:
        subscriber_emails.update(
            article.publisher.subscribed_readers.values_list('email', flat=True)
        )

    if subscriber_emails:
        send_mail(
            subject=f"New article: {article.title}",
            message=article.content,
            from_email='news@example.com',
            recipient_list=list(subscriber_emails),
            fail_silently=True,
        )

    # 2. POST the approved article to our own API endpoint, simulating
    #    external distribution while keeping everything inside the project.
    try:
        serialized = ArticleSerializer(article).data
        requests.post(
            request.build_absolute_uri('/api/approved/'),
            json=serialized,
            timeout=5,
        )
    except requests.exceptions.RequestException:
        # Don't let a failed simulated POST block the approval itself.
        pass

    return redirect('pending_articles')
