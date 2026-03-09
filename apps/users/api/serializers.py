from rest_framework import serializers
from apps.users.models import User, StudentProfile
from apps.academic.models import Grade


class GradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grade
        fields = (
            "id",
            "name",
        )


class StudentProfileSerializer(serializers.ModelSerializer):
    grade = GradeSerializer()

    class Meta:
        model = StudentProfile
        fields = (
            "id",
            "grade",
            "total_points",
            "completed_topics_count",
            "created_at",
            "updated_at",
        )


class MeSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "date_joined",
            "image",
            "profile",
        )

    def get_profile(self, obj):
        if obj.role == User.Role.STUDENT:
            try:
                profile = obj.student_profile
                return StudentProfileSerializer(profile).data
            except StudentProfile.DoesNotExist:
                return None
        return None

    def get_image(self, obj):
        request = self.context.get("request")

        if obj.image:
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url

        return None


class UserListSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "image",
        )

    def get_image(self, obj):
        request = self.context.get("request")

        if obj.image:
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url

        return None


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "password",
            "role",
        )

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
        )


class UserImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("image",)
