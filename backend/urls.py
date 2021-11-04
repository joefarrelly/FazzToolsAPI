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

profile = routers.DefaultRouter()
profile.register(r'users', views.ProfileUserView)
profile.register(r'usermounts', views.ProfileUserMountView)
# profile.register(r'userfiles', views.ProfileUserFileView)
profile.register(r'alts', views.ProfileAltView)
profile.register(r'altprofessions', views.ProfileAltProfessionView)
profile.register(r'altprofessiondatas', views.ProfileAltProfessionDataView)
profile.register(r'altequipments', views.ProfileAltEquipmentView)

data = routers.DefaultRouter()
data.register(r'professions', views.DataProfessionView)
data.register(r'professiontiers', views.DataProfessionTierView)
data.register(r'professionrecipes', views.DataProfessionRecipeView)
data.register(r'reagents', views.DataReagentView)
data.register(r'recipereagents', views.DataRecipeReagentView)
data.register(r'equipments', views.DataEquipmentView)
data.register(r'equipmentvariants', views.DataEquipmentVariantView)
data.register(r'mounts', views.DataMountView)

custom = routers.DefaultRouter()
custom.register(r'bnetlogin', views.BnetLogin, 'bnetlogin')
custom.register(r'scanalt', views.ScanAlt, 'scanalt')
custom.register(r'datascan', views.DataScan, 'datascan')
custom.register(r'fileupload', views.FileUpload, 'fileupload')

urlpatterns = [
    path('api/admin/', admin.site.urls),
    path('api/profile/', include(profile.urls)),
    path('api/data/', include(data.urls)),
    path('api/custom/', include(custom.urls)),
]
