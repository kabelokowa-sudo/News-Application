import requests
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required, permission_required
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render

from .forms import RegisterForm
from .models import Article
from .serializers import ArticleSerializer


def home(request):
    """Landing page. Shows role-specific info for logged-in users."""
    return render(request, 'news/home.html')


def register(request):
    """
    Front-end sign-up view. Lets a visitor create an account and pick
    a role (Reader, Editor, or Journalist). Saving the form creates the
    CustomUser, and the `sync_user_role` signal (signals.py) takes care
    of putting them in the matching Group so their permissions are set
    up immediately - no manual group-assignment needed here.
    """
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect('home')
    else:
        form = RegisterForm()

    return render(request, 'news/register.html', {'form': form})


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
