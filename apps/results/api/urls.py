from django.urls import path

from .views import AcademicStatsMeAPIView, LeaderboardAPIView


urlpatterns = [
    path("leaderboard/", LeaderboardAPIView.as_view(), name="leaderboard"),
    path("academic/stats/me/", AcademicStatsMeAPIView.as_view(), name="academic-stats-me"),
]
