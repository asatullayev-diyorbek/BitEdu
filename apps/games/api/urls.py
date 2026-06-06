from django.urls import path

from .views import (
    AnagramListAPIView,
    AnagramDetailAPIView,
    AnagramCheckAPIView,
    AnagramSubmitAPIView,
    QuizDifficultyListAPIView,
    QuizListAPIView,
    QuizDetailAPIView,
    QuizSubmitAPIView,
    AdminAnagramListCreateAPIView,
    AdminAnagramDetailAPIView,
    AdminQuizListCreateAPIView,
    AdminQuizDetailAPIView,
)

urlpatterns = [
    # ─── STUDENT: ANAGRAM ───
    path("anagrams/", AnagramListAPIView.as_view(), name="anagram-list"),
    path("anagrams/<uuid:id>/", AnagramDetailAPIView.as_view(), name="anagram-detail"),
    path("anagrams/<uuid:id>/check/", AnagramCheckAPIView.as_view(), name="anagram-check"),
    path("anagrams/<uuid:id>/submit/", AnagramSubmitAPIView.as_view(), name="anagram-submit"),

    # ─── STUDENT: QUIZ ───
    path("quizzes/difficulties/", QuizDifficultyListAPIView.as_view(), name="quiz-difficulties"),
    path("quizzes/", QuizListAPIView.as_view(), name="quiz-list"),
    path("quizzes/<uuid:id>/", QuizDetailAPIView.as_view(), name="quiz-detail"),
    path("quizzes/<uuid:id>/submit/", QuizSubmitAPIView.as_view(), name="quiz-submit"),

    # ─── ADMIN: ANAGRAM ───
    path("admin/anagrams/", AdminAnagramListCreateAPIView.as_view(), name="admin-anagram-list"),
    path("admin/anagrams/<uuid:id>/", AdminAnagramDetailAPIView.as_view(), name="admin-anagram-detail"),

    # ─── ADMIN: QUIZ ───
    path("admin/quizzes/", AdminQuizListCreateAPIView.as_view(), name="admin-quiz-list"),
    path("admin/quizzes/<uuid:id>/", AdminQuizDetailAPIView.as_view(), name="admin-quiz-detail"),
]
