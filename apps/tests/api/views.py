from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone


from rest_framework import generics
from rest_framework.permissions import IsAdminUser
from apps.tests.models import TestAnswer, TestAttempt, TestOption, TestQuestion, TopicProgress
from .serializers import AdminTestQuestionSerializer

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.academic.models import Topic
from apps.users.models import StudentProfile, User
from .serializers import (
    TestQuestion,
    TestOption,
    TopicProgress,
)
from utils.paginations import StandardPagination
from .serializers import (
    TestQuestionSerializer,
    TestSubmissionSerializer,
    TestSubmissionResultSerializer,
)

# O'tish chegarasi (50%)
PASS_THRESHOLD = 0.5

class StudentOnlyAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_student_profile(self, request):
        user = request.user
        if not hasattr(user, "role") or user.role != User.Role.STUDENT:
            raise PermissionDenied("Faqat o'quvchilar test topshirishi mumkin.")
        try:
            return user.student_profile
        except StudentProfile.DoesNotExist:
            raise ValidationError("Student profile mavjud emas.")

class TestQuestionListAPIView(StudentOnlyAPIView):
    def get(self, request):
        self.get_student_profile(request)

        queryset = (
            TestQuestion.objects
            .filter(is_active=True)
            .select_related("topic", "topic__subject", "topic__subject__grade")
            .prefetch_related("options")
        )

        topic_id = request.query_params.get("topic")
        search = request.query_params.get("search")
        
        if topic_id:
            queryset = queryset.filter(topic_id=topic_id)

        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )

        # Tartiblash
        ordering = request.query_params.get("ordering", "order")
        if ordering not in {"order", "created_at", "title", "-order", "-created_at"}:
            ordering = "order"
        queryset = queryset.order_by(ordering)

        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = TestQuestionSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

class TestSubmissionAPIView(StudentOnlyAPIView):
    def post(self, request):
        profile = self.get_student_profile(request)

        serializer = TestSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        topic_id = serializer.validated_data["topic_id"]
        submitted_answers = serializer.validated_data["answers"]

        topic = get_object_or_404(Topic, id=topic_id)

        # 1. Bazadagi barcha faol savollarni olish
        active_questions = TestQuestion.objects.filter(
            topic=topic, 
            is_active=True
        ).prefetch_related("options")
        
        total_questions_count = active_questions.count()
        if total_questions_count == 0:
            raise ValidationError("Ushbu mavzuda faol savollar topilmadi.")

        # Savollarni lug'atga yig'ish (tezkor qidiruv uchun)
        questions_dict = {q.id: q for q in active_questions}
        
        # 2. Tanlangan variantlarni bitta so'rovda olish
        option_ids = [a["selected_option_id"] for a in submitted_answers]
        options_dict = {
            o.id: o for o in TestOption.objects.filter(id__in=option_ids)
        }

        correct_count = 0
        answers_to_create = []

        # 3. Javoblarni solishtirish
        for item in submitted_answers:
            q_id = item["question_id"]
            o_id = item["selected_option_id"]

            question = questions_dict.get(q_id)
            option = options_dict.get(o_id)

            if not question:
                raise ValidationError(f"Savol (ID: {q_id}) ushbu mavzuga tegishli emas yoki faol emas.")
            
            if not option or option.question_id != question.id:
                raise ValidationError(f"Variant (ID: {o_id}) tanlangan savolga tegishli emas.")

            if option.is_correct:
                correct_count += 1
            
            answers_to_create.append(
                TestAnswer(
                    question=question,
                    selected_option=option,
                    is_correct=option.is_correct
                )
            )

        # 4. Natijani hisoblash (bazadagi jami savollarga nisbatan)
        passed = (correct_count / total_questions_count) >= PASS_THRESHOLD
        advice = "Yaxshi natija!" if passed else "Mavzuni qayta ko'rib chiqishingizni maslahat beramiz."

        with transaction.atomic():
            # Attempt yaratish
            attempt = TestAttempt.objects.create(
                student_profile=profile,
                topic=topic,
                total_questions=total_questions_count,
                correct_answers=correct_count,
                passed=passed,
            )

            # Javoblarni attemptga bog'lab saqlash
            for ans in answers_to_create:
                ans.attempt = attempt
            TestAnswer.objects.bulk_create(answers_to_create)

            # Progressni yangilash
            progress, _ = TopicProgress.objects.get_or_create(
                student_profile=profile,
                topic=topic,
            )

            previous_best = progress.best_score
            progress.attempts_count += 1
            progress.last_attempt_at = timezone.now()

            # Eng yaxshi natijani yangilash
            if correct_count > progress.best_score:
                progress.best_score = correct_count
            
            # Agar birinchi marta o'tgan bo'lsa
            newly_completed = False
            if passed and not progress.is_completed:
                progress.is_completed = True
                newly_completed = True
            
            progress.save()

            # Ballarni hisoblash: Faqat natija yaxshilansa ball beramiz
            # (Hozirgi to'g'ri javob - eski eng yaxshi natija) * 10 ball
            points_awarded = max(0, (correct_count - previous_best) * 10)
            if points_awarded > 0:
                profile.total_points += points_awarded

            if newly_completed:
                profile.completed_topics_count += 1

            profile.save()

        # 5. Natijani qaytarish
        result_payload = {
            "topic": {
                "id": str(topic.id),
                "title": topic.title,
                "subject": topic.subject.name,
                "grade": topic.subject.grade.name,
            },
            "score": correct_count,
            "total_questions": total_questions_count,
            "correct_answers": correct_count,
            "passed": passed,
            "points_awarded": points_awarded,
            "best_score": progress.best_score,
            "attempts_count": progress.attempts_count,
            "completed_topics_count": profile.completed_topics_count,
            "total_points": profile.total_points,
            "advice": advice,
        }

        return Response(TestSubmissionResultSerializer(result_payload).data)
    

# 1. Savollarni ko'rish va yangi (variantlari bilan) yaratish
class AdminTestQuestionListCreateAPIView(generics.ListCreateAPIView):
    # Bu yerda o'zingning Role == ADMIN tekshiruvingni qo'yishing mumkin
    permission_classes = [IsAuthenticated] 
    serializer_class = AdminTestQuestionSerializer

    def get_queryset(self):
        topic_id = self.request.query_params.get('topic')
        queryset = TestQuestion.objects.all().prefetch_related('options')
        if topic_id:
            queryset = queryset.filter(topic_id=topic_id)
        return queryset

# 2. Savolni tahrirlash, o'chirish yoki bittasini ko'rish
class AdminTestQuestionDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AdminTestQuestionSerializer
    queryset = TestQuestion.objects.all().prefetch_related('options')
    lookup_field = 'id'