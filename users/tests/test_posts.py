from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import Post, Follow, Hashtag

url_list = reverse("post-list")
def get_post_detail_url(post: Post):
    return reverse("post-detail", args=[post.id])


def post_create(author, content: str = "Old"):
    return Post.objects.create(
        author=author,
        content=content
    )


class PostApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="test@test.com",
            password="testpass123",
        )
        self.client.force_authenticate(user=self.user)

    def test_create_post(self):
        response = self.client.post(
            url_list,
            {"content": "My first post"},
            format="json",
        )
        num = Post.objects.count()
        post = Post.objects.first()
        self.assertEqual(post.author, self.user)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(num, 1)

    def test_update_own_post(self):
        post = post_create(author=self.user)

        url_detail = get_post_detail_url(post)
        response = self.client.patch(
            url_detail,
            {"content": "New"},
            format="json",
        )
        post.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(post.content, "New")

    def test_cannot_update_other_user_post(self):
        other_user = get_user_model().objects.create_user(
            email="other@test.com",
            password="testother123",
        )

        post = post_create(author=other_user)
        url = get_post_detail_url(post)
        response = self.client.patch(
            url,
            {"content": "New"},
            format="json"
        )
        post.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(post.content, "Old")

    def test_delete_own_post(self):
        post = post_create(author=self.user)
        url = get_post_detail_url(post)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            Post.objects.filter(id=post.id).exists()
        )

    def test_cannot_delete_other_user_post(self):
        other_user = get_user_model().objects.create_user(
            email="other@test.com",
            password="testother123",
        )
        post = post_create(author=other_user)
        url = get_post_detail_url(post)
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(
            Post.objects.filter(id=post.id).exists()
        )

    def test_feed_contains_own_posts(self):
        post_1 = post_create(
            author=self.user,
            content="First",
        )
        post_2 = post_create(
            author=self.user,
            content="Second",
        )

        response = self.client.get(url_list)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        post_ids = [post["id"] for post in response.data]

        self.assertIn(post_1.id, post_ids)
        self.assertIn(post_2.id, post_ids)

    def test_feed_contains_followed_user_posts(self):
        other_user = get_user_model().objects.create_user(
            email="other@test.com",
            password="testother123",
        )

        Follow.objects.create(
            follower=self.user,
            following=other_user,
        )

        post = post_create(
            author=other_user,
            content="Followed user post",
        )

        response = self.client.get(url_list)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        post_ids = [post_data["id"] for post_data in response.data]

        self.assertIn(post.id, post_ids)

    def test_feed_excludes_unfollowed_user_posts(self):
        other_user = get_user_model().objects.create_user(
            email="other@test.com",
            password="testother123",
        )

        post = post_create(
            author=other_user,
            content="Hidden post",
        )

        response = self.client.get(url_list)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        post_ids = [post_data["id"] for post_data in response.data]

        self.assertNotIn(post.id, post_ids)

    def test_unauthenticated_user_cannot_create_post(self):
        self.client.force_authenticate(user=None)

        response = self.client.post(
            url_list,
            {"content": "Unauthorized post"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
        self.assertEqual(Post.objects.count(), 0)

    def test_filter_posts_by_hashtag(self):
        python_tag = Hashtag.objects.create(name="python")
        django_tag = Hashtag.objects.create(name="django")

        post_python = post_create(
            author=self.user,
            content="Python post",
        )
        post_django = post_create(
            author=self.user,
            content="Django post",
        )

        post_python.hashtags.add(python_tag)
        post_django.hashtags.add(django_tag)

        response = self.client.get(
            url_list,
            {"hashtag": "python"},
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]["id"],
            post_python.id,
        )
