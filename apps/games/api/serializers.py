import random

from rest_framework import serializers

from apps.games.models import (
    AnagramGame,
    AnagramWord,
    QuizGame,
    QuizGameQuestion,
    QuizGameOption,
)


def _scramble(letters):
    """Harflarni aralashtiradi (iloji bo'lsa asl tartibdan farqli)."""
    shuffled = letters[:]
    if len(shuffled) > 1:
        for _ in range(10):
            random.shuffle(shuffled)
            if shuffled != letters:
                break
    return shuffled


# ─────────────────────────── ANAGRAM ───────────────────────────
class AnagramListSerializer(serializers.ModelSerializer):
    """Ro'yxat kartasi — so'zlar CHIQMAYDI."""
    played_count = serializers.IntegerField(read_only=True)
    is_completed = serializers.BooleanField(read_only=True)
    words_count = serializers.IntegerField(source="words.count", read_only=True)

    class Meta:
        model = AnagramGame
        fields = (
            "id",
            "title",
            "description",
            "xp",
            "difficulty",
            "played_count",
            "is_completed",
            "words_count",
        )


class AnagramWordPublicSerializer(serializers.ModelSerializer):
    """Bitta so'z — aralash harflar va uzunlik, asl so'z CHIQMAYDI."""
    scrambled_letters = serializers.SerializerMethodField()
    answer_length = serializers.SerializerMethodField()

    class Meta:
        model = AnagramWord
        fields = ("id", "order", "hint", "scrambled_letters", "answer_length")

    def get_scrambled_letters(self, obj):
        return _scramble(obj.letters)

    def get_answer_length(self, obj):
        return len(obj.text)


class AnagramDetailSerializer(serializers.ModelSerializer):
    """O'yin ekrani — 5 ta so'z (aralash harflar bilan), javoblar CHIQMAYDI."""
    played_count = serializers.IntegerField(read_only=True)
    is_completed = serializers.BooleanField(read_only=True)
    words = AnagramWordPublicSerializer(many=True, read_only=True)

    class Meta:
        model = AnagramGame
        fields = (
            "id",
            "title",
            "description",
            "xp",
            "difficulty",
            "played_count",
            "is_completed",
            "words",
        )


class AnagramCheckSerializer(serializers.Serializer):
    """Bitta so'zni tekshirish (DB ga yozmaydi, faqat to'g'ri/noto'g'ri)."""
    word_id = serializers.UUIDField()
    answer = serializers.CharField(max_length=64)


class AnagramAnswerItemSerializer(serializers.Serializer):
    word_id = serializers.UUIDField()
    answer = serializers.CharField(max_length=64)


class AnagramSubmitSerializer(serializers.Serializer):
    """Barcha so'zlar yakunlangach yuboriladi — XP shu yerda beriladi."""
    answers = AnagramAnswerItemSerializer(many=True)

    def validate_answers(self, value):
        if not value:
            raise serializers.ValidationError("Javoblar bo'sh bo'lishi mumkin emas.")
        return value


# ─────────────────────────── QUIZ ───────────────────────────
class QuizListSerializer(serializers.ModelSerializer):
    played_count = serializers.IntegerField(read_only=True)
    is_completed = serializers.BooleanField(read_only=True)

    class Meta:
        model = QuizGame
        fields = (
            "id",
            "title",
            "description",
            "xp",
            "difficulty",
            "played_count",
            "is_completed",
        )


class QuizOptionPublicSerializer(serializers.ModelSerializer):
    """is_correct CHIQMAYDI — o'yin ma'nosini saqlash uchun."""
    class Meta:
        model = QuizGameOption
        fields = ("id", "text")


class QuizQuestionPublicSerializer(serializers.ModelSerializer):
    options = QuizOptionPublicSerializer(many=True, read_only=True)

    class Meta:
        model = QuizGameQuestion
        fields = ("id", "text", "order", "options")


class QuizDetailSerializer(serializers.ModelSerializer):
    questions = QuizQuestionPublicSerializer(many=True, read_only=True)
    played_count = serializers.IntegerField(read_only=True)
    is_completed = serializers.BooleanField(read_only=True)

    class Meta:
        model = QuizGame
        fields = (
            "id",
            "title",
            "description",
            "xp",
            "difficulty",
            "played_count",
            "is_completed",
            "questions",
        )


class QuizAnswerItemSerializer(serializers.Serializer):
    question_id = serializers.UUIDField()
    selected_option_id = serializers.UUIDField()


class QuizSubmitSerializer(serializers.Serializer):
    answers = QuizAnswerItemSerializer(many=True)

    def validate_answers(self, value):
        if not value:
            raise serializers.ValidationError("Minimal bitta savolga javob berish lozim.")
        question_ids = [item["question_id"] for item in value]
        if len(question_ids) != len(set(question_ids)):
            raise serializers.ValidationError("Har bir savolga faqat bitta javob tanlash mumkin.")
        return value


# ─────────────────────────── NATIJA ───────────────────────────
class GameResultSerializer(serializers.Serializer):
    """Anagram va Quiz natija ekrani uchun umumiy javob formati."""
    is_correct = serializers.BooleanField()
    correct_count = serializers.IntegerField(required=False)
    total_questions = serializers.IntegerField(required=False)
    points_awarded = serializers.IntegerField()
    already_completed = serializers.BooleanField()
    attempts_count = serializers.IntegerField()
    total_points = serializers.IntegerField()
    message = serializers.CharField(allow_blank=True, required=False)


# ─────────────────────────── ADMIN ───────────────────────────
class AdminAnagramWordSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=False)

    class Meta:
        model = AnagramWord
        fields = ("id", "text", "hint", "order")


class AdminAnagramSerializer(serializers.ModelSerializer):
    words = AdminAnagramWordSerializer(many=True)

    class Meta:
        model = AnagramGame
        fields = (
            "id",
            "title",
            "description",
            "xp",
            "difficulty",
            "order",
            "is_active",
            "words",
            "created_at",
        )
        read_only_fields = ("id", "created_at")

    def _write_words(self, game, words_data):
        for w in words_data:
            w.pop("id", None)
            AnagramWord.objects.create(game=game, **w)

    def create(self, validated_data):
        words_data = validated_data.pop("words", [])
        game = AnagramGame.objects.create(**validated_data)
        self._write_words(game, words_data)
        return game

    def update(self, instance, validated_data):
        words_data = validated_data.pop("words", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if words_data is not None:
            instance.words.all().delete()
            self._write_words(instance, words_data)
        return instance


class AdminQuizOptionSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=False)

    class Meta:
        model = QuizGameOption
        fields = ("id", "text", "is_correct")


class AdminQuizQuestionSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=False)
    options = AdminQuizOptionSerializer(many=True)

    class Meta:
        model = QuizGameQuestion
        fields = ("id", "text", "order", "options")


class AdminQuizSerializer(serializers.ModelSerializer):
    questions = AdminQuizQuestionSerializer(many=True)

    class Meta:
        model = QuizGame
        fields = (
            "id",
            "title",
            "description",
            "difficulty",
            "xp",
            "order",
            "is_active",
            "questions",
            "created_at",
        )
        read_only_fields = ("id", "created_at")

    def _write_questions(self, quiz, questions_data):
        for q in questions_data:
            options_data = q.pop("options", [])
            q.pop("id", None)
            question = QuizGameQuestion.objects.create(quiz=quiz, **q)
            for opt in options_data:
                opt.pop("id", None)
                QuizGameOption.objects.create(question=question, **opt)

    def create(self, validated_data):
        questions_data = validated_data.pop("questions", [])
        quiz = QuizGame.objects.create(**validated_data)
        self._write_questions(quiz, questions_data)
        return quiz

    def update(self, instance, validated_data):
        questions_data = validated_data.pop("questions", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Eng xavfsiz yo'l: eski savol/variantlarni o'chirib qayta yozish
        if questions_data is not None:
            instance.questions.all().delete()
            self._write_questions(instance, questions_data)
        return instance
