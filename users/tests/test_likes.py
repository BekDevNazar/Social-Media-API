from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import Like, Post


class LikeApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="test@test.com",
            password="testpass123",
        )

        self.post = Post.objects.create(
            author=self.user,
            content="Test post",
        )

        self.client.force_authenticate(user=self.user)

    def test_like_post(self):
        url = reverse(
            "like",
            args=[self.post.id],
        )

        response = self.client.post(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertTrue(
            Like.objects.filter(
                user=self.user,
                post=self.post,
            ).exists()
        )

    def test_cannot_like_post_twice(self):
        Like.objects.create(
            user=self.user,
            post=self.post,
        )

        url = reverse(
            "like",
            args=[self.post.id],
        )

        response = self.client.post(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            Like.objects.filter(
                user=self.user,
                post=self.post,
            ).count(),
            1,
        )

    def test_unlike_post(self):
        Like.objects.create(
            user=self.user,
            post=self.post,
        )

        url = reverse(
            "like",
            args=[self.post.id],
        )

        response = self.client.delete(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(
            Like.objects.filter(
                user=self.user,
                post=self.post,
            ).exists()
        )
