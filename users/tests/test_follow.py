from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import Follow, Profile


def create_user_with_profile(email):
    user = get_user_model().objects.create_user(
        email=email,
        password="testpass123",
    )
    Profile.objects.create(user=user)
    return user


class FollowApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="test@test.com",
            password="testpass123",
        )
        Profile.objects.create(user=self.user)

        self.client.force_authenticate(user=self.user)

    def test_follow_user(self):
        other_user = create_user_with_profile(
            "other@test.com"
        )

        url = reverse(
            "profile-follow",
            args=[other_user.profile.id],
        )

        response = self.client.post(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertTrue(
            Follow.objects.filter(
                follower=self.user,
                following=other_user,
            ).exists()
        )

    def test_cannot_follow_yourself(self):
        url = reverse(
            "profile-follow",
            args=[self.user.profile.id],
        )

        response = self.client.post(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertFalse(
            Follow.objects.filter(
                follower=self.user,
                following=self.user,
            ).exists()
        )

    def test_unfollow_user(self):
        other_user = create_user_with_profile(
            "other@test.com"
        )

        Follow.objects.create(
            follower=self.user,
            following=other_user,
        )

        url = reverse(
            "profile-follow",
            args=[other_user.profile.id],
        )

        response = self.client.delete(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(
            Follow.objects.filter(
                follower=self.user,
                following=other_user,
            ).exists()
        )

