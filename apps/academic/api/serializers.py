from rest_framework import serializers
from apps.academic.models import Grade, Subject, Topic, TopicResource
from apps.tests import models
from apps.tests.models import TopicProgress


class GradeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Grade
        fields = (
            "id",
            "name",
            "created_at",
        )


class GradeShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grade
        fields = (
            "id",
            "name",
        )


class SubjectSerializer(serializers.ModelSerializer):

    grade = GradeShortSerializer(read_only=True)
    grade_id = serializers.UUIDField(write_only=True, required=False)

    topic_count = serializers.IntegerField(read_only=True)

    book_url = serializers.SerializerMethodField()
    book_file = serializers.FileField(required=False, write_only=True)

    image_url = serializers.SerializerMethodField()
    image_file = serializers.ImageField(write_only=True, required=False)

    class Meta:
        model = Subject
        fields = (
            "id",
            "name",
            "grade",
            "grade_id",
            "description",
            "book_file",
            "image_file",
            "image_url",
            "topic_count",
            "book_url",
            "book_pages",
            "created_at",
        )

    def get_book_url(self, obj):
        request = self.context.get("request")

        if obj.book_file:
            return request.build_absolute_uri(obj.book_file.url)

        return None


    def get_image_url(self, obj):
        request = self.context.get("request")

        if obj.image:
            return request.build_absolute_uri(obj.image.url)

        return None


    def create(self, validated_data):

        grade_id = validated_data.pop("grade_id")
        grade = Grade.objects.get(id=grade_id)

        image = validated_data.pop("image_file", None)
        book = validated_data.pop("book_file", None)

        grade = Grade.objects.get(id=grade_id)

        subject = Subject.objects.create(
            grade=grade,
            image=image,
            book_file=book,
            **validated_data
        )

        return subject


    def update(self, instance, validated_data):

        grade_id = validated_data.pop("grade_id", None)

        image = validated_data.pop("image_file", None)
        book = validated_data.pop("book_file", None)

        if grade_id:
            grade = Grade.objects.get(id=grade_id)
            instance.grade = grade

        if image:
            instance.image = image

        if book:
            instance.book_file = book

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        return instance


    def validate_book_file(self, value):

        if value.size > 50 * 1024 * 1024:
            raise serializers.ValidationError(
                "PDF hajmi 5MB dan oshmasligi kerak."
            )

        if not value.name.endswith(".pdf"):
            raise serializers.ValidationError(
                "Faqat PDF fayl yuklash mumkin."
            )

        return value


class TopicSerializer(serializers.ModelSerializer):
    subject_id = serializers.UUIDField(write_only=True)
    subject = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Topic
        fields = (
            "id",
            "title",
            "description",
            "video_url",
            "order",
            "is_active",
            "subject",
            "subject_id",
            "created_at",
        )
        read_only_fields = ("id", "created_at", "subject")

    def get_subject(self, obj):
        return {
            "id": str(obj.subject_id),
            "name": obj.subject.name,
            "grade": obj.subject.grade.name,
        }

    def validate_subject_id(self, value):
        if not Subject.objects.filter(id=value).exists():
            raise serializers.ValidationError("Fan topilmadi.")
        return value

    def validate_order(self, value):
        if value <= 0:
            raise serializers.ValidationError("Tartib raqami 1 dan katta bo‘lishi kerak.")
        return value

    def create(self, validated_data):
        subject_id = validated_data.pop("subject_id")
        subject = Subject.objects.get(id=subject_id)

        # bir subject ichida order takrorlanmasligi
        if Topic.objects.filter(subject=subject, order=validated_data.get("order")).exists():
            raise serializers.ValidationError(
                {"order": "Bu tartib raqami ushbu fan ichida allaqachon mavjud."}
            )

        return Topic.objects.create(subject=subject, **validated_data)


class TopicResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = TopicResource
        fields = ['id', 'title', 'description', 'file', 'url']


class SubjectShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['id', 'name']


class TopicResourceSerializer(serializers.ModelSerializer):
    # topic_id emas, aynan 'topic' deb yozamiz (Modeldagi FK nomi)
    topic = serializers.PrimaryKeyRelatedField(queryset=Topic.objects.all())

    class Meta:
        model = TopicResource
        fields = ['id', 'topic', 'title', 'description', 'file', 'url', 'created_at']


class TopicDetailSerializer(serializers.ModelSerializer):
    student_progress = serializers.SerializerMethodField()
    resources = TopicResourceSerializer(many=True, read_only=True)
    subject = SubjectShortSerializer(read_only=True) # ID emas, obyekt qaytadi

    class Meta:
        model = Topic
        fields = [
            'id', 'title', 'description', 'video_url', 
            'subject', 'student_progress', 'resources'
        ]
    
    def get_student_progress(self, obj):
        request = self.context.get('request')
        # request.user mavjudligini va talaba profilini tekshiramiz
        if request and request.user.is_authenticated and hasattr(request.user, 'student_profile'):
            progress = TopicProgress.objects.filter(
                student_profile=request.user.student_profile, 
                topic=obj
            ).first()
            
            if progress:
                return {
                    "best_score": progress.best_score,
                    "attempts_count": progress.attempts_count,
                    "is_completed": progress.is_completed
                }
        return None