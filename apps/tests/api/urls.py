from django.urls import path
from .views import (
    TestQuestionListAPIView, 
    TestSubmissionAPIView,
    AdminTestQuestionListCreateAPIView,
    AdminTestQuestionDetailAPIView
)

urlpatterns = [
    # --- STUDENT ---
    path("questions/", TestQuestionListAPIView.as_view(), name="test-questions"),
    path("submit/", TestSubmissionAPIView.as_view(), name="test-submit"),

    # --- ADMIN (Yangi qo'shildi) ---
    # GET: ?topic=UUID orqali savollarni olish, POST: Savol yaratish
    path("admin/questions/", AdminTestQuestionListCreateAPIView.as_view(), name="admin-test-list"),
    
    # GET, PATCH, DELETE: Savolni boshqarish
    path("admin/questions/<uuid:id>/", AdminTestQuestionDetailAPIView.as_view(), name="admin-test-detail"),
]