from celery import shared_task
from django.contrib.auth import get_user_model

from users.models import Hashtag, Post


@shared_task
def create_scheduled_post(user_id, content, hashtags=None):
    user = get_user_model().objects.get(id=user_id)

    post = Post.objects.create(
        author=user,
        content=content,
    )

    tags = []

    for name in hashtags or []:
        tag, _ = Hashtag.objects.get_or_create(name=name)
        tags.append(tag)

    post.hashtags.set(tags)

    return post.id
