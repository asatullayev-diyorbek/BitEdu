from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

# Modellaringni import qil
from apps.academic.models import Grade, Subject, Topic
from apps.users.models import User, StudentProfile 

class AdminDashboardAPIView(APIView):
    def get(self, request):
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # 1. UMUMIY STATISTIKA (Counts)
        stats = {
            "students": {
                "total": User.objects.filter(role="STUDENT").count(),
                "this_month": User.objects.filter(role="STUDENT", date_joined__gte=start_of_month).count()
            },
            "subjects": {
                "total": Subject.objects.count(),
                "this_month": Subject.objects.filter(created_at__gte=start_of_month).count()
            },
            "topics": {
                "total": Topic.objects.count(),
                "this_month": Topic.objects.filter(created_at__gte=start_of_month).count()
            },
            "grades": {
                "total": Grade.objects.count(),
                "this_month": Grade.objects.filter(created_at__gte=start_of_month).count()
            }
        }

        # 2. OXIRGI HARAKATLAR (Recent Activities)
        # Oxirgi 5 ta qo'shilgan fan, mavzu va sinflarni olamiz
        recent_topics = Topic.objects.select_related('subject').order_by('-created_at')[:2]
        recent_subjects = Subject.objects.select_related('grade').order_by('-created_at')[:2]
        recent_grades = Grade.objects.order_by('-created_at')[:2]

        activities = []

        for t in recent_topics:
            activities.append({
                "id": str(t.id),
                "type": "TOPIC",
                "title": f"Yangi mavzu qo'shildi: {t.title}",
                "description": f"Fan: {t.subject.name}",
                "time": t.created_at
            })

        for s in recent_subjects:
            activities.append({
                "id": str(s.id),
                "type": "SUBJECT",
                "title": f"Yangi fan yaratildi: {s.name}",
                "description": f"Sinf: {s.grade.name}",
                "time": s.created_at
            })

        for g in recent_grades:
            activities.append({
                "id": str(g.id),
                "type": "GRADE",
                "title": f"Yangi sinf ochildi: {g.name}",
                "description": "Tizimga yangi sinf bosqichi qo'shildi",
                "time": g.created_at
            })

        # Vaqt bo'yicha saralash (eng yangisi tepada)
        activities.sort(key=lambda x: x['time'], reverse=True)

        return Response({
            "status": 200,
            "message": "Success",
            "data": {
                "stats": stats,
                "recent_activities": activities[:10] # Faqat oxirgi 10 tasini qaytaramiz
            }
        })