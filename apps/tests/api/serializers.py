from rest_framework import serializers
from apps.tests.models import TestOption, TestQuestion, TopicProgress
from apps.academic.models import Topic

class TestOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestOption
        fields = ("id", "text", "is_correct") # is_correct qo'shildi (Admin uchun kerak)

class TestQuestionSerializer(serializers.ModelSerializer):
    options = TestOptionSerializer(many=True) # options endi ham o'qiladi, ham yoziladi
    topic_info = serializers.SerializerMethodField(read_only=True)
    topic_id = serializers.UUIDField(write_only=True) # Yaratishda UUID kerak

    class Meta:
        model = TestQuestion
        fields = (
            "id",
            "title",
            "description",
            "order",
            "is_active",
            "topic_id",   # Write-only
            "topic_info", # Read-only (Sinf, Fan ma'lumotlari bilan)
            "options",
        )

    def get_topic_info(self, obj):
        # Topic, Subject va Grade ma'lumotlarini bitta so'rovda chiqarish
        return {
            "id": str(obj.topic_id),
            "title": obj.topic.title,
            "grade": obj.topic.subject.grade.name,
            "subject": obj.topic.subject.name,
        }

    def create(self, validated_data):
        # Variantlarni ajratib olamiz
        options_data = validated_data.pop('options', [])
        # Savolni yaratamiz
        question = TestQuestion.objects.create(**validated_data)
        # Variantlarni yaratamiz
        for option in options_data:
            TestOption.objects.create(question=question, **option)
        return question

    def update(self, instance, validated_data):
        options_data = validated_data.pop('options', None)
        
        # Asosiy maydonlarni yangilash
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Variantlarni yangilash (Eski variantlarni o'chirib, yangisini yozish eng xavfsiz yo'l)
        if options_data is not None:
            instance.options.all().delete()
            for option in options_data:
                TestOption.objects.create(question=instance, **option)
        
        return instance

# --- SUBMISSION SERIALIZERS (Bular o'zgarmadi, lekin mantiqiy to'g'ri) ---

class QuestionAnswerSerializer(serializers.Serializer):
    question_id = serializers.UUIDField()
    selected_option_id = serializers.UUIDField()

class TestSubmissionSerializer(serializers.Serializer):
    topic_id = serializers.UUIDField()
    answers = QuestionAnswerSerializer(many=True)

    def validate_answers(self, value):
        if not value:
            raise serializers.ValidationError("Minimal bitta savolga javob berish lozim.")
        return value

    def validate(self, data):
        question_ids = [item["question_id"] for item in data.get("answers", [])]
        if len(question_ids) != len(set(question_ids)):
            raise serializers.ValidationError("Har bir savolga faqat bitta javob tanlash mumkin.")
        return data

class TestSubmissionResultSerializer(serializers.Serializer):
    # Bu serializer asosan Response formatini belgilash uchun (read_only)
    topic = serializers.DictField()
    score = serializers.IntegerField()
    total_questions = serializers.IntegerField()
    correct_answers = serializers.IntegerField()
    passed = serializers.BooleanField()
    points_awarded = serializers.IntegerField()
    best_score = serializers.IntegerField()
    attempts_count = serializers.IntegerField()
    completed_topics_count = serializers.IntegerField()
    total_points = serializers.IntegerField()
    advice = serializers.CharField(allow_blank=True, required=False)


class AdminTestOptionSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=False) # Tahrirlashda ID kerak bo'ladi

    class Meta:
        model = TestOption
        fields = ("id", "text", "is_correct")

class AdminTestQuestionSerializer(serializers.ModelSerializer):
    options = AdminTestOptionSerializer(many=True)

    class Meta:
        model = TestQuestion
        fields = ("id", "topic", "title", "description", "order", "is_active", "options")

    def create(self, validated_data):
        options_data = validated_data.pop('options', [])
        question = TestQuestion.objects.create(**validated_data)
        for option in options_data:
            TestOption.objects.create(question=question, **option)
        return question

    def update(self, instance, validated_data):
        options_data = validated_data.pop('options', None)
        
        # Asosiy maydonlarni yangilash
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Variantlarni yangilash (Eski variantlarni o'chirib, yangisini yozish eng toza yo'l)
        if options_data is not None:
            instance.options.all().delete()
            for option in options_data:
                TestOption.objects.create(question=instance, **option)
        
        return instance
    
