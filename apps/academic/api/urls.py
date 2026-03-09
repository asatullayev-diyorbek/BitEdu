from django.urls import path
from .views import GradeAPIView, GradeDetailAPIView, SubjectAPIView, SubjectDetailAPIView, TopicAPIView, TopicDetailAPIView

urlpatterns = [
    path("grades/", GradeAPIView.as_view()),
    path("grades/<uuid:id>/", GradeDetailAPIView.as_view()),
    path("subjects/", SubjectAPIView.as_view()),
    path("subjects/<uuid:id>/", SubjectDetailAPIView.as_view()),
    path("topics/", TopicAPIView.as_view()),
    path("topics/<uuid:id>/", TopicDetailAPIView.as_view()),
]
