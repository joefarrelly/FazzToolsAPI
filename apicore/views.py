from django.shortcuts import render
from rest_framework import viewsets
from .serializers import AltSerializer
from .models import Alt

# Create your views here.


class AltView(viewsets.ModelViewSet):
    serializer_class = AltSerializer
    queryset = Alt.objects.all()
