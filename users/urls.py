from django.urls import path, include
from rest_framework.routers import DefaultRouter

from users.views import (
    CreateTokenView,
    CreateUserView,
    FollowProfileView,
    FollowersMeView,
    FollowingMeView,
    LogoutView,
    ManageProfileView,
    ProfileDetailView,
    ProfileListView,
    PostCommentsView,
    PostView,
    LikeView,
    LikedPostsView,
    CommentDetailView,
)


router = DefaultRouter()
router.register("posts", PostView, basename="post")

urlpatterns = [
    path("", include(router.urls)),
    path("register/", CreateUserView.as_view(), name="create"),
    path("login/", CreateTokenView.as_view(), name="login"),
    path("profile/me/", ManageProfileView.as_view(), name="profile-manage"),
    path(
        "profile/me/following/",
        FollowingMeView.as_view(),
        name="following",
    ),
    path(
        "profile/me/followers/",
        FollowersMeView.as_view(),
        name="followers",
    ),
    path("logout/", LogoutView.as_view(), name="logout"),
    path(
        "profiles/<int:pk>/",
        ProfileDetailView.as_view(),
        name="profile-detail",
    ),
    path("profiles/", ProfileListView.as_view(), name="profile-list"),
    path(
        "profiles/<int:pk>/follow/",
        FollowProfileView.as_view(),
        name="profile-follow",
    ),
    path("posts/<int:pk>/like/", LikeView.as_view(), name="like"),
    path("profile/me/liked-posts/", LikedPostsView.as_view(), name="my-like"),
    path(
        "posts/<int:pk>/comments/",
        PostCommentsView.as_view(),
        name="post-comments",
    ),
    path(
        "comments/<int:pk>/",
        CommentDetailView.as_view(),
        name="comment-detail",
),
]
