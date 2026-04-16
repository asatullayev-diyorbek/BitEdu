from django.urls import path
from .views import ChangePasswordAPIView, LoginAPIView, RefreshAPIView, LogoutAPIView, StudentDashboardAPIView
from apps.users.api.views import MeAPIView, StudentRegistrationAPIView
from .views import (
    UserListCreateAPIView,
    UserRetrieveUpdateAPIView,
    UserUpdateImageAPIView,
)


urlpatterns = [
    path("login/", LoginAPIView.as_view()),
    path("refresh/", RefreshAPIView.as_view()),
    path("logout/", LogoutAPIView.as_view()),
    path("register/", StudentRegistrationAPIView.as_view(), name="student-register"),
    path("me/", MeAPIView.as_view()),
    path("user/", UserListCreateAPIView.as_view()),
    path("user/<uuid:id>/", UserRetrieveUpdateAPIView.as_view()),
    path("user/<uuid:id>/update-image/", UserUpdateImageAPIView.as_view()),

    path("change-password/", ChangePasswordAPIView.as_view(), name="change-password"),

    path("student/dashboard/stats/", StudentDashboardAPIView.as_view(), name="student-dashboard"),
]
