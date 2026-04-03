from django.db.models import Avg, F, Count, ExpressionWrapper, FloatField, Q
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from rest_framework.response import Response
from django.forms import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from utils.paginations import StandardPagination
from apps.results.api.serializers import LeaderboardSerializer, StudentStatsSerializer
from apps.users.models import StudentProfile, User
from apps.tests.models import TestAttempt, TopicProgress
class AcademicStatsMeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_student_profile(self, user):
        # 1. Roli tekshirish (auth tizimingizga qarab)
        if not hasattr(user, "role") or user.role != User.Role.STUDENT:
            raise PermissionDenied("Faqat o'quvchilar ushbu statistikani ko'rishi mumkin.")
        
        # 2. StudentProfile borligini aniq tekshirish
        profile = getattr(user, "student_profile", None)
        if not profile:
            raise ValidationError({"detail": "Foydalanuvchiga tegishli student profili topilmadi."})
        return profile

    def get(self, request):
        try:
            profile = self.get_student_profile(request.user)
            
            # DB darajasida statistikani hisoblash (Python loop'dan ancha tez)
            stats = TestAttempt.objects.filter(student_profile=profile).aggregate(
                taken=Count('id'),
                passed_count=Count('id', filter=Q(passed=True)),
                avg_score=Avg(
                    ExpressionWrapper(
                        F('correct_answers') * 100.0 / F('total_questions'),
                        output_field=FloatField()
                    ),
                    filter=Q(total_questions__gt=0)
                )
            )

            # Rank hisoblashda modelda indexing bo'lmasa, bu qism sekin ishlashi mumkin
            rank_filter = (
                Q(total_points__gt=profile.total_points) |
                Q(total_points=profile.total_points, completed_topics_count__gt=profile.completed_topics_count) |
                Q(total_points=profile.total_points, completed_topics_count=profile.completed_topics_count, created_at__lt=profile.created_at)
            )
            rank = StudentProfile.objects.filter(rank_filter).count() + 1

            # Recent topics (NULL tekshiruvi va xatoliklar bilan)
            recent_progress = (
                TopicProgress.objects
                .select_related("topic", "topic__subject")
                .filter(student_profile=profile, topic__isnull=False)
                .order_by("-last_attempt_at")[:5]
            )

            recent_topics = []
            for record in recent_progress:
                if record.topic and record.topic.subject:
                    recent_topics.append({
                        "id": str(record.topic.id),
                        "title": record.topic.title,
                        "subject_name": record.topic.subject.name,
                    })

            # Top 3 (select_related orqali DB so'rovni kamaytirish)
            top_three = (
                StudentProfile.objects
                .select_related("user")
                .order_by("-total_points", "-completed_topics_count", "-created_at")[:3]
            )

            leaderboard_top3 = [
                {
                    "user_id": str(member.user_id),
                    "full_name": member.user.get_full_name(),
                    "points": member.total_points,
                    "rank": idx,
                }
                for idx, member in enumerate(top_three, start=1)
            ]

            stats_payload = {
                "total_points": profile.total_points,
                "rank": rank,
                "topics_completed": profile.completed_topics_count,
                "subjects_started": TopicProgress.objects.filter(student_profile=profile).values("topic__subject").distinct().count(),
                "average_score": round(stats['avg_score'] or 0.0, 2),
                "tests_passed": stats['passed_count'],
                "tests_taken": stats['taken'],
                "recent_topics": recent_topics,
                "leaderboard_top3": leaderboard_top3,
            }

            serializer = StudentStatsSerializer(stats_payload)
            return Response(serializer.data)

        except Exception as e:
            # Server logiga xatoni yozamiz (Sentry yoki logger orqali)
            print(f"Stats Error: {e}") 
            return Response(
                {"detail": "Statistikani yuklashda kutilmagan xatolik yuz berdi."},
                status=500
            )
        

class LeaderboardAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            grade_filter = request.query_params.get("grade")
            
            # select_related muhim, lekin filterda xato bo'lsa handle qilish kerak
            queryset = StudentProfile.objects.select_related("user", "grade").all()

            if grade_filter:
                # Agar grade_id UUID bo'lsa va noto'g'ri string kelsa, ValueError berishi mumkin
                try:
                    queryset = queryset.filter(
                        Q(grade_id=grade_filter) |
                        Q(grade__name__iexact=grade_filter)
                    )
                except (ValueError, ValidationError):
                    return Response({"detail": "Sinf filtri noto'g'ri formatda."}, status=400)

            queryset = queryset.order_by("-total_points", "-completed_topics_count", "-created_at")

            paginator = StandardPagination()
            page = paginator.paginate_queryset(queryset, request)
            
            if page is not None:
                serializer = LeaderboardSerializer(page, many=True)
                data = serializer.data

                # Pagination rank hisoblash mantiqi
                page_obj = getattr(paginator, "page", None)
                page_number = page_obj.number if page_obj else 1
                page_size = paginator.get_page_size(request) or 10
                start_rank = (page_number - 1) * page_size

                for idx, entry in enumerate(data, start=1):
                    entry["rank"] = start_rank + idx

                return paginator.get_paginated_response(data)
            
            return Response({"detail": "Ma'lumot topilmadi."}, status=404)

        except Exception as e:
            print(f"Leaderboard Error: {e}")
            return Response({"detail": "Serverda texnik xatolik."}, status=500)
