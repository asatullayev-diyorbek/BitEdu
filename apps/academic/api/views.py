import traceback

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.db.models import Q, Count, ProtectedError
from django.shortcuts import get_object_or_404
from django.db import IntegrityError, utils
from django.forms import ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework import generics

from apps.academic.models import Grade, Subject, Topic, TopicResource
from .serializers import GradeSerializer, SubjectSerializer, TopicResourceSerializer, TopicSerializer
from utils.paginations import StandardPagination
from .serializers import TopicDetailSerializer


class GradeAPIView(APIView):

    def get(self, request):

        queryset = Grade.objects.all()

        search = request.query_params.get("search")
        ordering = request.query_params.get("ordering")

        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
            )

        if ordering:
            queryset = queryset.order_by(ordering)

        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)

        serializer = GradeSerializer(page, many=True)

        return paginator.get_paginated_response(serializer.data)

    def post(self, request):

        serializer = GradeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )


class GradeDetailAPIView(APIView):

    def get(self, request, id):

        grade = get_object_or_404(Grade, id=id)

        serializer = GradeSerializer(grade)

        return Response(serializer.data)


    def patch(self, request, id):

        grade = get_object_or_404(Grade, id=id)

        serializer = GradeSerializer(
            grade,
            data=request.data,
            partial=True
        )

        serializer.is_valid(raise_exception=True)

        try:
            serializer.save()
        except utils.IntegrityError:
            return Response(
                {"message": "Grade already exists"},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(serializer.data)


    def delete(self, request, id):
        grade = get_object_or_404(Grade, id=id)

        try:
            grade.delete()
        except ProtectedError:
            return Response(
                {
                    "message": "Bu sinfni o'chirib bo'lmaydi, chunki unga bog'langan fanlar mavjud."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {"message": "Sinf muvaffaqiyatli o'chirildi."},
            status=status.HTTP_204_NO_CONTENT
        )


class SubjectAPIView(APIView):

    def get(self, request):

        try:

            queryset = (
                Subject.objects
                .select_related("grade")
                .annotate(topic_count=Count("topics"))
                .order_by("-created_at")
            )

            search = request.query_params.get("search")
            grade = request.query_params.get("grade")
            ordering = request.query_params.get("ordering")

            if search:
                queryset = queryset.filter(
                    Q(name__icontains=search)
                )

            if grade:
                queryset = queryset.filter(
                    grade_id=grade
                )

            if ordering:
                queryset = queryset.order_by(ordering)

            paginator = StandardPagination()
            page = paginator.paginate_queryset(queryset, request)

            serializer = SubjectSerializer(
                page,
                many=True,
                context={"request": request}
            )

            return paginator.get_paginated_response(serializer.data)

        except Exception:
            return Response(
                {"message": "Ma'lumotlarni olishda xatolik yuz berdi."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request):

        serializer = SubjectSerializer(
            data=request.data,
            context={"request": request}
        )

        try:

            serializer.is_valid(raise_exception=True)

            subject = serializer.save()

        except ValidationError:
            return Response(
                {"message": "Yuborilgan ma'lumotlar noto‘g‘ri."},
                status=status.HTTP_400_BAD_REQUEST
            )

        except IntegrityError:
            return Response(
                {"message": "Bu fan allaqachon mavjud."},
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            print(e)
            return Response(
                {"message": "Fan yaratishda xatolik yuz berdi."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            SubjectSerializer(
                subject,
                context={"request": request}
            ).data,
            status=status.HTTP_201_CREATED
        )


class SubjectDetailAPIView(APIView):

    def get(self, request, id):

        try:
            subject = (
                Subject.objects
                .select_related("grade")
                .annotate(topic_count=Count("topics"))
                .get(id=id)
            )

        except Subject.DoesNotExist:
            return Response(
                {"message": "Fan topilmadi."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = SubjectSerializer(
            subject,
            context={"request": request}
        )

        return Response(serializer.data)

    def patch(self, request, id):

        subject = get_object_or_404(Subject, id=id)

        serializer = SubjectSerializer(
            subject,
            data=request.data,
            partial=True,
            context={"request": request}
        )

        try:

            serializer.is_valid(raise_exception=True)

            subject = serializer.save()

        except IntegrityError:
            return Response(
                {"message": "Bu fan allaqachon mavjud."},
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            print(e)
            return Response(
                {"message": "Fan yangilashda xatolik yuz berdi."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            SubjectSerializer(
                subject,
                context={"request": request}
            ).data
        )

    def delete(self, request, id):

        subject = get_object_or_404(Subject, id=id)

        try:
            subject.delete()

        except ProtectedError:
            return Response(
                {
                    "message": "Bu fanni o‘chirib bo‘lmaydi, chunki unga bog‘langan darslar mavjud."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception:
            return Response(
                {"message": "Fanni o‘chirishda xatolik yuz berdi."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            {"message": "Fan muvaffaqiyatli o‘chirildi."},
            status=status.HTTP_204_NO_CONTENT
        )


class TopicAPIView(APIView):

    def get(self, request):
        try:
            queryset = Topic.objects.select_related("subject").order_by("order")

            subject = request.query_params.get("subject")
            search = request.query_params.get("search")
            ordering = request.query_params.get("ordering")

            if subject:
                queryset = queryset.filter(subject_id=subject)

            if search:
                queryset = queryset.filter(
                    Q(title__icontains=search) |
                    Q(description__icontains=search)
                )

            if ordering:
                queryset = queryset.order_by(ordering)

            paginator = StandardPagination()
            page = paginator.paginate_queryset(queryset, request)

            serializer = TopicSerializer(page, many=True)

            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            print(e)
            return Response(
                {"message": "Darslarni olishda xatolik yuz berdi."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request):
        serializer = TopicSerializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
            topic = serializer.save()

        except IntegrityError:
            return Response(
                {"message": "Bu dars allaqachon mavjud."},
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            print(e)
            return Response(
                {
                    "message": "Validation error",
                    "errors": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            TopicSerializer(topic).data,
            status=status.HTTP_201_CREATED
        )


class TopicDetailAPIView(APIView):
    def get(self, request, id):
        try:
            topic_queryset = Topic.objects.select_related(
                'subject', 
                'subject__grade'
            ).prefetch_related('resources')
            
            topic = get_object_or_404(topic_queryset, id=id)
            print(f"--- DEBUG: Topic topildi: {topic.title} ---")

            serializer = TopicDetailSerializer(topic, context={'request': request})
            
            data = serializer.data

            return Response({
                "status": 200,
                "message": "Success",
                "data": data
            }, status=status.HTTP_200_OK)

        except Topic.DoesNotExist:
            print(f"--- ERROR: Topic topilmadi (ID: {id}) ---")
            return Response({
                "status": 404,
                "message": "Dars topilmadi (Bazada yo'q)."
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            print("--- !!! SERVERDA XATOLIK YUZ BERDI !!! ---")
            print(f"Xato turi: {type(e).__name__}")
            print(f"Xato xabari: {str(e)}")
            traceback.print_exc() 
            
            return Response({
                "status": 500,
                "message": f"Serverda xatolik: {str(e)}",
                "trace": type(e).__name__
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, id):

        topic = get_object_or_404(Topic, id=id)

        serializer = TopicSerializer(
            topic,
            data=request.data,
            partial=True
        )

        try:
            serializer.is_valid(raise_exception=True)
            topic = serializer.save()

        except ValidationError:
            return Response(
                {
                    "status": 400,
                    "message": "Validation error",
                    "data": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        except IntegrityError:
            return Response(
                {
                    "status": 400,
                    "message": "Bu tartib raqami allaqachon mavjud.",
                    "data": {}
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response({
            "status": 200,
            "message": "Dars yangilandi.",
            "data": TopicSerializer(topic).data
        })


    def delete(self, request, id):

        topic = get_object_or_404(Topic, id=id)

        try:
            topic.delete()

        except Exception:
            return Response(
                {
                    "status": 400,
                    "message": "Darsni o‘chirishda xatolik yuz berdi.",
                    "data": {}
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {
                "status": 200,
                "message": "Dars muvaffaqiyatli o‘chirildi.",
                "data": {}
            }
        )


class TopicResourceListCreateAPIView(generics.ListCreateAPIView):
    """ Resurslarni ko'rish va yangi qo'shish """
    queryset = TopicResource.objects.all()
    serializer_class = TopicResourceSerializer
    permission_classes = [permissions.IsAdminUser]
    
    # MANA SHU QATOR FAYL YUKLASH UCHUN SHART!
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get_queryset(self):
        topic_id = self.request.query_params.get('topic')
        if topic_id:
            return self.queryset.filter(topic_id=topic_id)
        return self.queryset

    def post(self, request, *args, **kwargs):
        # Agar xato chiqsa, terminalda aynan nima xatoligini ko'rish uchun try-except
        try:
            return super().post(request, *args, **kwargs)
        except Exception as e:
            print("--- RESOURCE POST ERROR ---")
            print(f"Xato turi: {type(e).__name__}")
            print(f"Xato xabari: {str(e)}")
            return Response(
                {"message": str(e), "status": 500}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class TopicResourceDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """ Resursni tahrirlash va o'chirish """
    queryset = TopicResource.objects.all()
    serializer_class = TopicResourceSerializer
    permission_classes = [permissions.IsAdminUser]
    
    # Tahrirlashda ham fayl yangilanishi mumkin bo'lsa:
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    lookup_field = 'id'