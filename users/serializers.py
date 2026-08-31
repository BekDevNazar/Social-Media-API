from django.contrib.auth import authenticate, get_user_model
from django.utils.translation import gettext as _
from rest_framework import serializers

from users.models import Profile, Follow, Post, Hashtag, Comment


class AuthTokenSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(
        style={"input_type": "password"},
        trim_whitespace=False,
        write_only=True,
    )

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        if email and password:
            user = authenticate(
                request=self.context.get("request"),
                username=email,
                password=password
            )

            # The authenticate call simply returns None for is_active=False
            # users. (Assuming the default ModelBackend authentication
            # backend.)
            if not user:
                msg = _("Unable to log in with provided credentials.")
                raise serializers.ValidationError(
                    msg, code="authorization"
                )
        else:
            msg = _('Must include "email" and "password".')
            raise serializers.ValidationError(msg, code="authorization")

        attrs["user"] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = [
            "id",
            "email",
            "password",
            "first_name",
            "last_name",
            "is_staff"
        ]
        read_only_fields = ["id", "is_staff"]
        extra_kwargs = {"password": {"write_only": True, "min_length": 5}}

    def create(self, validated_data):
        user = get_user_model().objects.create_user(**validated_data)
        Profile.objects.create(user=user)
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        user = super().update(instance, validated_data)

        if password:
            user.set_password(password)
            user.save(update_fields=["password"])

        return user


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = [
            "id",
            "first_name",
            "last_name",
        ]


class ProfileSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = [
            "id",
            "user",
            "bio",
            "image"
        ]
        read_only_fields = ["id"]


class FollowSerializer(serializers.ModelSerializer):
    following = UserProfileSerializer(read_only=True)

    class Meta:
        model = Follow
        fields = [
            "following",
        ]


class FollowerSerializer(serializers.ModelSerializer):
    follower = UserProfileSerializer(read_only=True)

    class Meta:
        model = Follow
        fields = [
            "follower",
        ]


class PostSerializer(serializers.ModelSerializer):
    author = UserProfileSerializer(read_only=True)
    hashtags = serializers.ListField(
        child=serializers.CharField(max_length=20),
        required=False,
        write_only=True
    )
    likes_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Post
        fields = [
            "id",
            "author",
            "content",
            "image",
            "hashtags",
            "created_at",
            "updated_at",
            "likes_count",
        ]

    def create(self, validated_data):
        hashtags = validated_data.pop("hashtags", [])
        post = Post.objects.create(**validated_data)
        tags = []

        for hashtag in hashtags:
            tag, _ = Hashtag.objects.get_or_create(
                name=hashtag
            )
            tags.append(tag)

        post.hashtags.set(tags)
        return post


class HashtagSerializer(serializers.ModelSerializer):
    def validate_name(self, value):
        if value.startswith("#"):
            raise serializers.ValidationError(
                "Should not start with #."
            )

        return value

    class Meta:
        model = Hashtag
        fields = [
            "name"
        ]


class CommentSerializer(serializers.ModelSerializer):
    author = UserProfileSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = [
            "id",
            "author",
            "content",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "author",
            "created_at",
            "updated_at",
        ]
