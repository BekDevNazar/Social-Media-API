from django.db.models import Q, Count
from django.shortcuts import get_object_or_404
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import IsAuthenticated
from rest_framework.settings import api_settings
from rest_framework import generics, viewsets
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

from users.tasks import create_scheduled_post
from users.models import Profile, Follow, Post, Like, Comment
from users.permission import IsOwnerOrReadOnly
from users.serializers import (
    AuthTokenSerializer,
    UserSerializer,
    ProfileSerializer,
    FollowSerializer,
    FollowerSerializer,
    PostSerializer,
    CommentSerializer, SchedulePostSerializer
)


class CreateTokenView(ObtainAuthToken):
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES
    serializer_class = AuthTokenSerializer


class CreateUserView(generics.CreateAPIView):
    serializer_class = UserSerializer


class ManageProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user.profile


class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        request=None,
        responses={
            204: OpenApiResponse(
                description="Logged out successfully."
            ),
        },
    )
    def post(self, request):
        request.auth.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProfileDetailView(generics.RetrieveAPIView):
    serializer_class = ProfileSerializer
    permission_classes = (IsAuthenticated,)
    queryset = Profile.objects.select_related("user")


class ProfileListView(generics.ListAPIView):
    serializer_class = ProfileSerializer
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="search",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Search users by first or last name",
                required=False,
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Profile.objects.select_related("user")
        search = self.request.query_params.get("search")

        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search)
                | Q(user__last_name__icontains=search)
            )

        return queryset


class FollowingMeView(generics.ListAPIView):
    serializer_class = FollowSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return Follow.objects.filter(
            follower=self.request.user
        )


class FollowersMeView(generics.ListAPIView):
    serializer_class = FollowerSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return Follow.objects.filter(
            following=self.request.user
        )


class FollowProfileView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        request=None,
        responses={
            201: OpenApiResponse(
                description="User followed successfully."
            ),
            400: OpenApiResponse(
                description="Cannot follow this user."
            ),
        },
    )
    def post(self, request, pk):
        profile = get_object_or_404(Profile, pk=pk)

        if profile.user == request.user:
            return Response(
                {"detail": "You cannot follow yourself."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        follow, created = Follow.objects.get_or_create(
            follower=request.user,
            following=profile.user
        )

        if not created:
            return Response(
                {"detail": "You already follow this user."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"detail": "Followed successfully."},
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        request=None,
        responses={
            204: OpenApiResponse(
                description="User unfollowed successfully."
            ),
        },
    )
    def delete(self, request, pk):
        profile = get_object_or_404(Profile, pk=pk)

        follow = get_object_or_404(
            Follow,
            follower=request.user,
            following=profile.user,
        )

        follow.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PostView(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    permission_classes = (
        IsAuthenticated,
        IsOwnerOrReadOnly,
    )

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="hashtag",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter posts by hashtag",
                required=False,
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        queryset = (Post.objects
                    .select_related("author")
                    .prefetch_related("hashtags"))

        if self.action == "list":
            following_ids = Follow.objects.filter(
                follower=self.request.user
            ).values_list(
                "following_id",
                flat=True,
            )

            queryset = queryset.filter(
                Q(author=self.request.user)
                | Q(author_id__in=following_ids)
            )
            hashtag = self.request.query_params.get("hashtag")
            if hashtag:
                queryset = queryset.filter(
                    hashtags__name__iexact=hashtag
                )

        return (queryset.order_by("-created_at")
                .annotate(likes_count=Count("likes")))

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class LikeView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        request=None,
        responses={
            201: OpenApiResponse(
                description="Post liked successfully."
            ),
            400: OpenApiResponse(
                description="Post already liked."
            ),
        },
    )
    def post(self, request, pk):
        post = get_object_or_404(Post, pk=pk)

        like, created = Like.objects.get_or_create(
            user=request.user,
            post=post
        )
        if not created:
            return Response(
                {"detail": "You already liked this post."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {"detail": "Liked successfully."},
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        request=None,
        responses={
            204: OpenApiResponse(
                description="Like removed successfully."
            ),
        },
    )
    def delete(self, request, pk):
        post = get_object_or_404(Post, pk=pk)

        like = get_object_or_404(
            Like,
            user=request.user,
            post=post
        )
        like.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class LikedPostsView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = PostSerializer

    def get_queryset(self):
        return (
            Post.objects
            .filter(likes__user=self.request.user)
            .select_related("author")
            .prefetch_related("hashtags")
            .annotate(likes_count=Count("likes"))
            .order_by("-created_at")
        )


class PostCommentsView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CommentSerializer

    def get_queryset(self):
        return (
            Comment.objects
            .filter(post_id=self.kwargs["pk"])
            .select_related("author")
            .order_by("created_at")
        )
    def perform_create(self, serializer):
        post = get_object_or_404(
            Post,
            pk=self.kwargs["pk"]
        )
        serializer.save(
            author=self.request.user,
            post=post
        )


class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly)
    serializer_class = CommentSerializer

    queryset = Comment.objects.select_related("author")


class SchedulePostView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        request=SchedulePostSerializer,
        responses={
            202: OpenApiResponse(
                description="Post successfully scheduled."
            ),
        },
    )
    def post(self, request):
        serializer = SchedulePostSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        task = create_scheduled_post.apply_async(
            args=[
                request.user.id,
                data["content"],
                data["hashtags"],
            ],
            eta=data["scheduled_at"],
        )

        return Response(
            {
                "detail": "Post scheduled successfully.",
                "task_id": task.id,
                "scheduled_at": data["scheduled_at"],
            },
            status=status.HTTP_202_ACCEPTED,
        )
