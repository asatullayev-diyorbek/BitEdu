# pylint: disable=unused-argument
from rest_framework import serializers

from apps.users.models import StudentProfile


class LeaderboardSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username")
    full_name = serializers.SerializerMethodField()
    grade_name = serializers.CharField(source="grade.name")

    class Meta:
        model = StudentProfile
        fields = (
            "id",
            "username",
            "full_name",
            "grade_name",
            "total_points",
            "completed_topics_count",
        )

    def get_full_name(self, obj):
        return obj.user.get_full_name()


class RecentTopicSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    title = serializers.CharField()
    subject_name = serializers.CharField()


class LeaderboardTop3Serializer(serializers.Serializer):
    user_id = serializers.UUIDField()
    full_name = serializers.CharField()
    points = serializers.IntegerField()
    rank = serializers.IntegerField()


class StudentStatsSerializer(serializers.Serializer):
    total_points = serializers.IntegerField()
    rank = serializers.IntegerField()
    topics_completed = serializers.IntegerField()
    subjects_started = serializers.IntegerField()
    average_score = serializers.FloatField()
    tests_passed = serializers.IntegerField()
    tests_taken = serializers.IntegerField()
    recent_topics = RecentTopicSerializer(many=True)
    leaderboard_top3 = LeaderboardTop3Serializer(many=True)
