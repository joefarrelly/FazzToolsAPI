from django.shortcuts import render
from rest_framework import viewsets
from .serializers import AltSerializer, AltProfessionSerializer, AltAchievementSerializer, AltQuestCompletedSerializer, AltMediaSerializer, EquipmentSerializer, AltEquipmentSerializer
from .models import Alt, AltProfession, AltAchievement, AltQuestCompleted, AltMedia, Equipment, AltEquipment

# Create your views here.


class AltView(viewsets.ModelViewSet):
    serializer_class = AltSerializer
    queryset = Alt.objects.all()


class AltProfessionView(viewsets.ModelViewSet):
    serializer_class = AltProfessionSerializer
    queryset = AltProfession.objects.all()


class AltAchievementView(viewsets.ModelViewSet):
    serializer_class = AltAchievementSerializer
    queryset = AltAchievement.objects.all()


class AltQuestCompletedView(viewsets.ModelViewSet):
    serializer_class = AltQuestCompletedSerializer
    queryset = AltQuestCompleted.objects.all()


class AltMediaView(viewsets.ModelViewSet):
    serializer_class = AltMediaSerializer
    queryset = AltMedia.objects.all()


class EquipmentView(viewsets.ModelViewSet):
    serializer_class = EquipmentSerializer
    queryset = Equipment.objects.all()


class AltEquipmentView(viewsets.ModelViewSet):
    serializer_class = AltEquipmentSerializer
    queryset = AltEquipment.objects.all()
