from rest_framework import serializers
from apps.users.models import User, StudentProfile
from apps.academic.models import Grade


class GradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grade
        fields = (
            "id",
            "name",
        )


class StudentProfileSerializer(serializers.ModelSerializer):
    grade = GradeSerializer()

    class Meta:
        model = StudentProfile
        fields = (
            "id",
            "grade",
            "total_points",
            "completed_topics_count",
            "created_at",
            "updated_at",
        )


class MeSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "date_joined",
            "image",
            "profile",
        )

    def get_profile(self, obj):
        if obj.role == User.Role.STUDENT:
            try:
                profile = obj.student_profile
                return StudentProfileSerializer(profile).data
            except StudentProfile.DoesNotExist:
                return None
        return None

    def get_image(self, obj):
        request = self.context.get("request")

        if obj.image:
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url

        return None


class UserListSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "image",
        )

    def get_image(self, obj):
        request = self.context.get("request")

        if obj.image:
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url

        return None


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "password",
            "role",
        )

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    # grade_id ni tashqaridan qabul qilish uchun qo'shamiz
    grade_id = serializers.UUIDField(write_only=True, required=False)

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "grade_id", # Bu yerga qo'shdik
        )

    def update(self, instance, validated_data):
        # 1. grade_id ni ma'lumotlar ichidan sug'urib olamiz
        grade_id = validated_data.pop('grade_id', None)
        
        # 2. Asosiy User ma'lumotlarini yangilaymiz (ism, familiya va h.k.)
        instance = super().update(instance, validated_data)

        # 3. Agar grade_id kelgan bo'lsa, StudentProfile ni ham yangilaymiz
        if grade_id:
            try:
                # StudentProfile mavjudligini tekshiramiz yoki yaratamiz
                profile, created = StudentProfile.objects.get_or_create(user=instance)
                
                # Grade obyektini bazadan topamiz
                grade = Grade.objects.get(id=grade_id)
                
                # Profilga yangi sinfni biriktiramiz
                profile.grade = grade
                profile.save()
            except Grade.DoesNotExist:
                raise serializers.ValidationError({"grade_id": "Bunday sinf topilmadi."})
            except Exception as e:
                raise serializers.ValidationError({"detail": f"Profilni yangilashda xatolik: {str(e)}"})

        return instance


class UserImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("image",)
        

class StudentListSerializer(serializers.ModelSerializer):
    grade = serializers.CharField(source='student_profile.grade.name', read_only=True)
    grade_id = serializers.UUIDField(source='student_profile.grade.id', read_only=True)
    points = serializers.IntegerField(source='student_profile.total_points', read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 
            'username', 
            'first_name', 
            'last_name', 
            'email', 
            'image', 
            'grade', 
            'grade_id',
            'points', 
            'date_joined'
        )