from django.db import transaction
from django.db.models import F, Count, Q, Exists, OuterRef
from django.shortcuts import get_object_or_404

from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.users.models import StudentProfile, User
from apps.games.models import (
    AnagramGame,
    AnagramWord,
    QuizGame,
    QuizGameQuestion,
    QuizGameOption,
    GameAttempt,
    GameDifficulty,
)
from utils.paginations import StandardPagination
from .serializers import (
    AnagramListSerializer,
    AnagramDetailSerializer,
    AnagramCheckSerializer,
    AnagramSubmitSerializer,
    QuizListSerializer,
    QuizDetailSerializer,
    QuizSubmitSerializer,
    GameResultSerializer,
    AdminAnagramSerializer,
    AdminQuizSerializer,
)


# ─────────────────────────── BASE ───────────────────────────
class StudentOnlyAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_student_profile(self, request):
        user = request.user
        if not hasattr(user, "role") or user.role != User.Role.STUDENT:
            raise PermissionDenied("Faqat o'quvchilar o'yin o'ynashi mumkin.")
        try:
            return user.student_profile
        except StudentProfile.DoesNotExist:
            raise ValidationError("Student profile mavjud emas.")


def _annotate_progress(queryset, profile, attempt_fk):
    """
    Har bir o'yinga shu o'quvchi uchun `played_count` va `is_completed` qo'shadi.
    attempt_fk: "anagram" yoki "quiz".
    """
    completed = GameAttempt.objects.filter(
        student_profile=profile, is_correct=True, **{attempt_fk: OuterRef("pk")}
    )
    return queryset.annotate(
        played_count=Count(
            "attempts",
            filter=Q(attempts__student_profile=profile),
        ),
        is_completed=Exists(completed),
    )


# ─────────────────────────── ANAGRAM ───────────────────────────
class AnagramListAPIView(StudentOnlyAPIView):
    def get(self, request):
        profile = self.get_student_profile(request)
        queryset = AnagramGame.objects.filter(is_active=True)
        queryset = _annotate_progress(queryset, profile, "anagram")

        difficulty = request.query_params.get("difficulty")
        if difficulty in GameDifficulty.values:
            queryset = queryset.filter(difficulty=difficulty)

        # annotate Meta ordering'ni yo'qotadi — aniq tartib qo'yamiz
        queryset = queryset.order_by("order", "created_at")

        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = AnagramListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class AnagramDetailAPIView(StudentOnlyAPIView):
    def get(self, request, id):
        profile = self.get_student_profile(request)
        queryset = _annotate_progress(
            AnagramGame.objects.filter(is_active=True), profile, "anagram"
        ).prefetch_related("words")
        game = get_object_or_404(queryset, id=id)
        return Response(AnagramDetailSerializer(game).data)


class AnagramCheckAPIView(StudentOnlyAPIView):
    """Bitta so'zni tekshiradi (DB ga yozmaydi) — 'birini topsa keyingisiga o'tadi' uchun."""
    def post(self, request, id):
        self.get_student_profile(request)
        game = get_object_or_404(AnagramGame, id=id, is_active=True)

        serializer = AnagramCheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        word = get_object_or_404(
            AnagramWord, id=serializer.validated_data["word_id"], game=game
        )
        submitted = serializer.validated_data["answer"].strip().upper()
        is_correct = submitted == word.text.strip().upper()

        return Response({
            "word_id": str(word.id),
            "is_correct": is_correct,
        })


class AnagramSubmitAPIView(StudentOnlyAPIView):
    """Barcha so'zlar yakunlangach chaqiriladi — barchasi to'g'ri bo'lsa XP beriladi."""
    def post(self, request, id):
        profile = self.get_student_profile(request)
        game = get_object_or_404(AnagramGame, id=id, is_active=True)

        serializer = AnagramSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        submitted_answers = serializer.validated_data["answers"]

        words = list(AnagramWord.objects.filter(game=game))
        total_words = len(words)
        if total_words == 0:
            raise ValidationError("Bu o'yinda so'zlar mavjud emas.")

        words_dict = {w.id: w for w in words}
        correct_count = 0
        for item in submitted_answers:
            word = words_dict.get(item["word_id"])
            if not word:
                raise ValidationError("So'z ushbu o'yinga tegishli emas.")
            if item["answer"].strip().upper() == word.text.strip().upper():
                correct_count += 1

        is_correct = correct_count == total_words

        with transaction.atomic():
            already_completed = GameAttempt.objects.filter(
                student_profile=profile,
                anagram=game,
                is_correct=True,
            ).exists()

            points = game.xp if (is_correct and not already_completed) else 0

            GameAttempt.objects.create(
                student_profile=profile,
                game_type=GameAttempt.GameType.ANAGRAM,
                anagram=game,
                is_correct=is_correct,
                points_awarded=points,
            )

            if points:
                StudentProfile.objects.filter(pk=profile.pk).update(
                    total_points=F("total_points") + points
                )

            attempts_count = GameAttempt.objects.filter(
                student_profile=profile, anagram=game
            ).count()

        profile.refresh_from_db(fields=["total_points"])

        if is_correct and points:
            message = f"Ajoyib! Barcha so'zlarni topdingiz. +{points} XP qo'shildi."
        elif is_correct:
            message = "Barcha so'zlar topildi! Lekin bu o'yin avval bajarilgan, ball qo'shilmaydi."
        else:
            message = "Hamma so'z to'g'ri emas. Qayta urinib ko'ring."

        payload = {
            "is_correct": is_correct,
            "correct_count": correct_count,
            "total_questions": total_words,
            "points_awarded": points,
            "already_completed": already_completed,
            "attempts_count": attempts_count,
            "total_points": profile.total_points,
            "message": message,
        }
        return Response(GameResultSerializer(payload).data)


# ─────────────────────────── QUIZ ───────────────────────────
class QuizDifficultyListAPIView(StudentOnlyAPIView):
    """Qiyinlik tanlash ekrani: har bir daraja va undagi kvizlar soni."""
    def get(self, request):
        self.get_student_profile(request)
        counts = {
            row["difficulty"]: row["c"]
            for row in (
                QuizGame.objects.filter(is_active=True)
                .values("difficulty")
                .annotate(c=Count("id"))
            )
        }
        data = [
            {
                "key": choice.value,
                "label": choice.label,
                "count": counts.get(choice.value, 0),
            }
            for choice in GameDifficulty
        ]
        return Response(data)


class QuizListAPIView(StudentOnlyAPIView):
    def get(self, request):
        profile = self.get_student_profile(request)
        queryset = QuizGame.objects.filter(is_active=True)
        queryset = _annotate_progress(queryset, profile, "quiz")

        difficulty = request.query_params.get("difficulty")
        if difficulty in GameDifficulty.values:
            queryset = queryset.filter(difficulty=difficulty)

        # annotate Meta ordering'ni yo'qotadi — aniq tartib qo'yamiz
        queryset = queryset.order_by("difficulty", "order")

        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = QuizListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class QuizDetailAPIView(StudentOnlyAPIView):
    def get(self, request, id):
        profile = self.get_student_profile(request)
        queryset = _annotate_progress(
            QuizGame.objects.filter(is_active=True), profile, "quiz"
        ).prefetch_related("questions__options")
        quiz = get_object_or_404(queryset, id=id)
        return Response(QuizDetailSerializer(quiz).data)


class QuizSubmitAPIView(StudentOnlyAPIView):
    def post(self, request, id):
        profile = self.get_student_profile(request)
        quiz = get_object_or_404(QuizGame, id=id, is_active=True)

        serializer = QuizSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        submitted_answers = serializer.validated_data["answers"]

        active_questions = list(
            QuizGameQuestion.objects.filter(quiz=quiz).prefetch_related("options")
        )
        total_questions = len(active_questions)
        if total_questions == 0:
            raise ValidationError("Ushbu kvizda savollar mavjud emas.")

        questions_dict = {q.id: q for q in active_questions}
        option_ids = [a["selected_option_id"] for a in submitted_answers]
        options_dict = {
            o.id: o for o in QuizGameOption.objects.filter(id__in=option_ids)
        }

        correct_count = 0
        for item in submitted_answers:
            question = questions_dict.get(item["question_id"])
            option = options_dict.get(item["selected_option_id"])
            if not question:
                raise ValidationError("Savol ushbu kvizga tegishli emas.")
            if not option or option.question_id != question.id:
                raise ValidationError("Variant tanlangan savolga tegishli emas.")
            if option.is_correct:
                correct_count += 1

        # To'liq to'g'ri = barcha savolga to'g'ri javob
        is_correct = correct_count == total_questions

        with transaction.atomic():
            already_completed = GameAttempt.objects.filter(
                student_profile=profile,
                quiz=quiz,
                is_correct=True,
            ).exists()

            points = quiz.xp if (is_correct and not already_completed) else 0

            GameAttempt.objects.create(
                student_profile=profile,
                game_type=GameAttempt.GameType.QUIZ,
                quiz=quiz,
                is_correct=is_correct,
                points_awarded=points,
            )

            if points:
                StudentProfile.objects.filter(pk=profile.pk).update(
                    total_points=F("total_points") + points
                )

            attempts_count = GameAttempt.objects.filter(
                student_profile=profile, quiz=quiz
            ).count()

        profile.refresh_from_db(fields=["total_points"])

        if is_correct and points:
            message = f"Barobar! +{points} XP qo'shildi."
        elif is_correct:
            message = "To'g'ri! Lekin bu kviz avval bajarilgan, ball qo'shilmaydi."
        else:
            message = "Hammasi to'g'ri emas. Qayta urinib ko'ring."

        payload = {
            "is_correct": is_correct,
            "correct_count": correct_count,
            "total_questions": total_questions,
            "points_awarded": points,
            "already_completed": already_completed,
            "attempts_count": attempts_count,
            "total_points": profile.total_points,
            "message": message,
        }
        return Response(GameResultSerializer(payload).data)


# ─────────────────────────── ADMIN ───────────────────────────
class IsAdminRole(IsAuthenticated):
    def has_permission(self, request, view):
        base = super().has_permission(request, view)
        return base and getattr(request.user, "role", None) == User.Role.ADMIN


class AdminAnagramListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = AdminAnagramSerializer
    queryset = AnagramGame.objects.all()


class AdminAnagramDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = AdminAnagramSerializer
    queryset = AnagramGame.objects.all()
    lookup_field = "id"


class AdminQuizListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = AdminQuizSerializer

    def get_queryset(self):
        qs = QuizGame.objects.all().prefetch_related("questions__options")
        difficulty = self.request.query_params.get("difficulty")
        if difficulty in GameDifficulty.values:
            qs = qs.filter(difficulty=difficulty)
        return qs


class AdminQuizDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = AdminQuizSerializer
    queryset = QuizGame.objects.all().prefetch_related("questions__options")
    lookup_field = "id"
