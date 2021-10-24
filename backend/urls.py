"""backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from apicore import views

router = routers.DefaultRouter()
router.register(r'users', views.FazzToolsUserView)
router.register(r'alts', views.AltView)
router.register(r'professions', views.ProfessionView)
router.register(r'professiontiers', views.ProfessionTierView)
router.register(r'professionrecipes', views.ProfessionRecipeView)
router.register(r'altprofessions', views.AltProfessionView)
router.register(r'altprofessiondatas', views.AltProfessionDataView)
router.register(r'equipments', views.EquipmentView)
router.register(r'altequipments', views.AltEquipmentView)
router.register(r'bnetlogin', views.BnetLogin, 'bnetlogin')
router.register(r'scanalt', views.ScanAlt, 'scanalt')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
]
