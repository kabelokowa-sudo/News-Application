from unittest.mock import patch

from django.core import mail
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from .models import CustomUser, Publisher, Article, Newsletter


def make_user(username, role):
    """
    Shortcut for creating a test user with a given role. Gives them a
    fake but valid-format email, since sending mail to an empty
    address silently fails and would break the approval flow test.
    """
    return CustomUser.objects.create_user(
        username=username,
        password='testpass123',
        role=role,
        email=f'{username}@example.com',
    )


class ArticleAPITests(APITestCase):
    """Tests for the article API - permissions, roles, subscriptions."""

    def setUp(self):
        self.reader = make_user('reader1', 'reader')
        self.editor = make_user('editor1', 'editor')
        self.journalist = make_user('journalist1', 'journalist')
        self.other_journalist = make_user('journalist2', 'journalist')

        self.publisher = Publisher.objects.create(name='Daily Test')

        self.approved_article = Article.objects.create(
            title='Approved Piece',
            content='Content here.',
            author=self.journalist,
            publisher=self.publisher,
            approved=True,
        )
        self.unapproved_article = Article.objects.create(
            title='Pending Piece',
            content='Draft content.',
            author=self.journalist,
            approved=False,
        )

    def test_unauthenticated_user_cannot_access_articles(self):
        response = self.client.get('/api/articles/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_reader_can_list_approved_articles(self):
        self.client.force_authenticate(user=self.reader)
        response = self.client.get('/api/articles/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = [a['title'] for a in response.data]
        self.assertIn('Approved Piece', titles)
        self.assertNotIn('Pending Piece', titles)

    def test_reader_cannot_create_article(self):
        self.client.force_authenticate(user=self.reader)
        response = self.client.post('/api/articles/', {
            'title': 'Reader Attempt', 'content': 'Should fail',
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_journalist_can_create_article(self):
        self.client.force_authenticate(user=self.journalist)
        response = self.client.post('/api/articles/', {
            'title': 'New Article', 'content': 'Some content',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # author should come from the logged-in user, not the request body
        created = Article.objects.get(title='New Article')
        self.assertEqual(created.author, self.journalist)

    def test_journalist_cannot_update_others_article(self):
        self.client.force_authenticate(user=self.other_journalist)
        response = self.client.put(
            f'/api/articles/{self.approved_article.id}/',
            {'title': 'Hijacked', 'content': 'Not yours'}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_editor_can_update_any_article(self):
        self.client.force_authenticate(user=self.editor)
        response = self.client.put(
            f'/api/articles/{self.approved_article.id}/',
            {'title': 'Edited by Editor', 'content': 'Updated content'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_editor_can_delete_article(self):
        self.client.force_authenticate(user=self.editor)
        response = self.client.delete(f'/api/articles/{self.unapproved_article.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Article.objects.filter(id=self.unapproved_article.id).exists())

    def test_reader_sees_only_subscribed_content(self):
        other_publisher = Publisher.objects.create(name='Other Publisher')
        _ = Article.objects.create(
            title='Other Publisher Article',
            content='Not subscribed to this one.',
            author=self.other_journalist,
            publisher=other_publisher,
            approved=True,
        )
        self.reader.subscriptions_to_publishers.add(self.publisher)

        self.client.force_authenticate(user=self.reader)
        response = self.client.get('/api/articles/subscribed/')
        titles = [a['title'] for a in response.data]
        self.assertIn('Approved Piece', titles)
        self.assertNotIn('Other Publisher Article', titles)


class NewsletterTests(APITestCase):
    """Basic newsletter creation and article association."""

    def setUp(self):
        self.journalist = make_user('newsletter_journalist', 'journalist')
        self.reader = make_user('newsletter_reader', 'reader')
        self.article = Article.objects.create(
            title='Featured Article',
            content='Content',
            author=self.journalist,
            approved=True,
        )

    def test_journalist_can_create_newsletter(self):
        newsletter = Newsletter.objects.create(
            title='Weekly Roundup',
            description='Top stories',
            author=self.journalist,
        )
        newsletter.articles.add(self.article)
        self.assertEqual(newsletter.articles.count(), 1)
        self.assertEqual(newsletter.author, self.journalist)


class ApprovalFlowTests(TestCase):
    """
    Tests for the editor approval view - checking the email goes out
    and the /api/approved/ call gets made. Mocked so it doesn't
    actually hit the network during tests.
    """

    def setUp(self):
        self.editor = make_user('approval_editor', 'editor')
        self.journalist = make_user('approval_journalist', 'journalist')
        self.reader = make_user('approval_reader', 'reader')

        self.reader.subscriptions_to_journalists.add(self.journalist)

        self.article = Article.objects.create(
            title='Breaking News',
            content='Something happened.',
            author=self.journalist,
            approved=False,
        )
        self.client.force_login(self.editor)

    @patch('news.views.requests.post')
    def test_approve_article_sends_email_and_logs_to_api(self, mock_post):
        response = self.client.post(
            reverse('approve_article', args=[self.article.id])
        )
        self.article.refresh_from_db()

        self.assertEqual(response.status_code, 302)  # redirects after approving
        self.assertTrue(self.article.approved)

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.reader.email, mail.outbox[0].to) if self.reader.email else None

        mock_post.assert_called_once()

    def test_reader_cannot_access_approval_view(self):
        self.client.force_login(self.reader)
        response = self.client.get(reverse('pending_articles'))
        self.assertEqual(response.status_code, 403)

    def test_debug_editor_permission(self):
        print("Editor groups:", list(self.editor.groups.values_list('name', flat=True)))
        print("Editor has change_article:", self.editor.has_perm('news.change_article'))
        print("Editor all perms:", self.editor.get_all_permissions())