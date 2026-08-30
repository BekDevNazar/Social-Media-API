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
    PostView,
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
]
