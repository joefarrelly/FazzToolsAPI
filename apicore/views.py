from django.shortcuts import render
from rest_framework import viewsets
from .serializers import AltSerializer, AltProfessionSerializer
from .models import Alt, AltProfession

# Create your views here.


class AltView(viewsets.ModelViewSet):
    serializer_class = AltSerializer
    queryset = Alt.objects.all()


class AltProfessionView(viewsets.ModelViewSet):
    serializer_class = AltProfessionSerializer
    queryset = AltProfession.objects.all()
