from django.urls import path

from apps.academic.api.dashboard import AdminDashboardAPIView
from .views import GradeAPIView, GradeDetailAPIView, SubjectAPIView, SubjectDetailAPIView, TopicAPIView, TopicDetailAPIView, TopicResourceDetailAPIView, TopicResourceListCreateAPIView

urlpatterns = [
    path("grades/", GradeAPIView.as_view()),
    path("grades/<uuid:id>/", GradeDetailAPIView.as_view()),
    path("subjects/", SubjectAPIView.as_view()),
    path("subjects/<uuid:id>/", SubjectDetailAPIView.as_view()),
    path("topics/", TopicAPIView.as_view()),
    path("topics/<uuid:id>/", TopicDetailAPIView.as_view(), name="topic-detail"),

    path('resources/', TopicResourceListCreateAPIView.as_view(), name='resource-list-create'),
    path('resources/<uuid:id>/', TopicResourceDetailAPIView.as_view(), name='resource-detail'),

    path("dashboard/stats/", AdminDashboardAPIView.as_view(), name="admin-dashboard-stats"),
]
