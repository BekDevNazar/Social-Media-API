from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import Comment, Post


class CommentApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="test@test.com",
            password="testpass123",
        )

        self.post = Post.objects.create(
            author=self.user,
            content="Post",
        )

        self.client.force_authenticate(user=self.user)

    def test_create_comment(self):
        url = reverse(
            "post-comments",
            args=[self.post.id],
        )

        response = self.client.post(
            url,
            {"content": "My comment"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        comment = Comment.objects.first()

        self.assertEqual(comment.content, "My comment")
        self.assertEqual(comment.author, self.user)
        self.assertEqual(comment.post, self.post)

    def test_update_own_comment(self):
        comment = Comment.objects.create(
            author=self.user,
            post=self.post,
            content="Old comment",
        )

        url = reverse(
            "comment-detail",
            args=[comment.id],
        )

        response = self.client.patch(
            url,
            {"content": "New comment"},
            format="json",
        )

        comment.refresh_from_db()

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            comment.content,
            "New comment",
        )

    def test_cannot_update_other_user_comment(self):
        other_user = get_user_model().objects.create_user(
            email="other@test.com",
            password="testpass123",
        )

        comment = Comment.objects.create(
            author=other_user,
            post=self.post,
            content="Other comment",
        )

        url = reverse(
            "comment-detail",
            args=[comment.id],
        )

        response = self.client.patch(
            url,
            {"content": "Hacked comment"},
            format="json",
        )

        comment.refresh_from_db()

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(
            comment.content,
            "Other comment",
        )
