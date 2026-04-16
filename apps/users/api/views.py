import logging

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import filters, generics, status
from rest_framework.permissions import IsAuthenticated

from apps.users.models import StudentProfile
from .serializers import MeSerializer, StudentListSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from django_filters.rest_framework import DjangoFilterBackend
from apps.tests.models import TestAttempt, TopicProgress
from django.db.models import Avg, Sum

from apps.users.api.serializers import (
    StudentListSerializer,
    UserCreateSerializer, UserImageSerializer, UserListSerializer, UserUpdateSerializer,
    UserListSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    UserImageSerializer,
    StudentRegistrationSerializer,
)

from django.contrib.auth import authenticate, get_user_model, update_session_auth_hash

User = get_user_model()


class MeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = MeSerializer(request.user, context={'request': request})
        return Response(serializer.data)


class StudentRegistrationAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = StudentRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # JWT token yaratish
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': MeSerializer(user, context={'request': request}).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserListCreateAPIView(generics.ListCreateAPIView):
    queryset = User.objects.all().order_by("-date_joined")
    permission_classes = [IsAuthenticated]

    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    ]

    filterset_fields = ["role"]

    ordering_fields = ["date_joined"]

    search_fields = ["username", "email"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return UserCreateSerializer
        return UserListSerializer


# RETRIEVE + UPDATE
class UserRetrieveUpdateAPIView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return UserUpdateSerializer
        return UserListSerializer


# UPDATE IMAGE
class UserUpdateImageAPIView(generics.UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserImageSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)


# Authentication
class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response(
                {"detail": "Username and password are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(username=username, password=password)

        if user is None:
            return Response(
                {"detail": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_active:
            return Response(
                {"detail": "User is inactive"},
                status=status.HTTP_403_FORBIDDEN,
            )

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "id": str(user.id),
                    "username": user.username,
                    "full_name": user.get_full_name(),
                    "role": user.role,
                    "image": request.build_absolute_uri(user.image.url) if user.image else None,
                },
            },
            status=status.HTTP_200_OK,
        )


class RefreshAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = TokenRefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        return Response(
            serializer.validated_data,
            status=status.HTTP_200_OK,
        )


class LogoutAPIView(APIView):
    def post(self, request):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response(
                {"detail": "Refresh token is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            return Response(
                {"detail": "Invalid refresh token"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"detail": "Logout successful"},
            status=status.HTTP_200_OK,
        )


class ChangePasswordAPIView(APIView):
    """
    Faqat parolni almashtirish uchun alohida API.
    Eski parolni tekshirish shart!
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")

        # 1. Ma'lumotlar borligini tekshiramiz
        if not old_password or not new_password:
            return Response(
                {"message": "Eski va yangi parollarni kiritish shart!"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Eski parolni tekshirish (Bazadagi bilan)
        if not user.check_password(old_password):
            return Response(
                {"message": {"old_password": ["Eski parol noto'g'ri. Iltimos, qaytadan urinib ko'ring."]}}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3. Yangi parolni o'rnatish
        # Django'da set_password() parolni hash qilib saqlaydi
        user.set_password(new_password)
        user.save()
        
        # Parol o'zgargandan keyin session o'chib ketmasligi uchun
        update_session_auth_hash(request, user)
        
        return Response(
            {"status": 200, "message": "Parol muvaffaqiyatli yangilandi. Endi xotirjam bo'lsang bo'ladi! ✨"}, 
            status=status.HTTP_200_OK
        )

logger = logging.getLogger(__name__)
class StudentDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        try:
            # 1. PROFILNI TEKSHIRISH
            try:
                profile = user.student_profile
            except Exception:
                return Response({
                    "status": 404,
                    "message": "Error",
                    "data": {"detail": "Student profili topilmadi. Avval profil yarating."}
                }, status=status.HTTP_404_NOT_FOUND)

            # 2. TEST STATISTIKASI (Correct answers bo'yicha)
            stats = {
                "total_points": profile.total_points,
                "completed_topics_count": profile.completed_topics_count,
                "tests_taken": 0,
                "average_score": 0
            }

            try:
                attempts = TestAttempt.objects.filter(student_profile=profile)
                stats["tests_taken"] = attempts.count()
                
                if stats["tests_taken"] > 0:
                    total_correct = attempts.aggregate(Sum('correct_answers'))['correct_answers__sum'] or 0
                    total_q = attempts.aggregate(Sum('total_questions'))['total_questions__sum'] or 0
                    if total_q > 0:
                        stats["average_score"] = round((total_correct / total_q) * 100, 1)
            except Exception as e:
                logger.warning(f"Statistika hisoblashda xato: {str(e)}")

            # 3. REYTING (Global Rank)
            rank = 1
            try:
                rank = StudentProfile.objects.filter(total_points__gt=profile.total_points).count() + 1
            except Exception as e:
                logger.warning(f"Rank hisoblashda xato: {str(e)}")

            # 4. OXIRGI MAVZULAR (Model fieldlariga aniq moslandi)
            recent_topics = []
            try:
                recent_qs = TopicProgress.objects.filter(student_profile=profile)\
                    .select_related('topic', 'topic__subject')\
                    .order_by('-last_attempt_at')[:5]

                recent_topics = [
                    {
                        "id": str(progress.topic.id),
                        "title": progress.topic.title,
                        "subject_name": progress.topic.subject.name,
                        "status": "Tugallangan" if progress.is_completed else "Davom etmoqda",
                        "time": progress.last_attempt_at
                    } for progress in recent_qs
                ]
            except Exception as e:
                logger.warning(f"Mavzularni yuklashda xato: {str(e)}")

            # 5. TOP 3 (Mini Leaderboard)
            leaderboard_top3 = []
            try:
                top_3_qs = StudentProfile.objects.select_related('user').filter(
                user__role=User.Role.STUDENT,
                user__is_active=True         
            ).order_by('-total_points')[:3]
                leaderboard_top3 = [
                    {
                        "full_name": p.user.get_full_name() or p.user.username,
                        "points": p.total_points
                    } for p in top_3_qs
                ]
            except Exception as e:
                logger.warning(f"Leaderboard yuklashda xato: {str(e)}")

            # 6. YAKUNIY JAVOB (Success)
            return Response({
                "status": 200,
                "message": "Success",
                "data": {
                    "full_name": user.get_full_name() or user.username,
                    "rank": rank,
                    "total_points": stats["total_points"],
                    "completed_topics_count": stats["completed_topics_count"],
                    "average_score": stats["average_score"],
                    "tests_taken": stats["tests_taken"],
                    "recent_topics": recent_topics,
                    "leaderboard_top3": leaderboard_top3
                }
            }, status=status.HTTP_200_OK)

        except Exception as global_error:
            # AGAR UMUMIY PORTLASH BO'LSA (500 o'rniga detail keladi)
            logger.error(f"StudentDashboardAPIView Global xatolik: {str(global_error)}")
            return Response({
                "status": 500,
                "message": "Internal Server Error",
                "data": {"detail": str(global_error)}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class StudentListAPIView(generics.ListAPIView):
    # Faqat studentlarni olamiz va profil/sinfni JOIN qilamiz (tez ishlashi uchun)
    queryset = User.objects.filter(role='STUDENT').select_related(
        'student_profile', 
        'student_profile__grade'
    ).order_by('-date_joined')
    
    serializer_class = StudentListSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Sinf bo'yicha filter: student_profile__grade
    filterset_fields = ['student_profile__grade']
    
    # Ism, familiya va username bo'yicha qidiruv
    search_fields = ['first_name', 'last_name', 'username', 'email']
