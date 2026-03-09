from django.urls import path
from .views import LoginAPIView, RefreshAPIView, LogoutAPIView
from apps.users.api.views import MeAPIView
from .views import (
    UserListCreateAPIView,
    UserRetrieveUpdateAPIView,
    UserUpdateImageAPIView,
)


urlpatterns = [
    path("login/", LoginAPIView.as_view()),
    path("refresh/", RefreshAPIView.as_view()),
    path("logout/", LogoutAPIView.as_view()),
    path("me/", MeAPIView.as_view()),
    path("user/", UserListCreateAPIView.as_view()),
    path("user/<uuid:id>/", UserRetrieveUpdateAPIView.as_view()),
    path("user/<uuid:id>/update-image/", UserUpdateImageAPIView.as_view()),
]
