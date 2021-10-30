from django.contrib import admin
# from .models import FazzToolsUser, Alt, Profession, ProfessionTier, ProfessionRecipe, AltProfession, AltProfessionData, Equipment, AltEquipment
from .models import *

# Register your models here.

admin.site.register(ProfileUser)
admin.site.register(ProfileAlt)
admin.site.register(DataProfession)
admin.site.register(DataProfessionTier)
admin.site.register(DataProfessionRecipe)
admin.site.register(ProfileAltProfession)
admin.site.register(ProfileAltProfessionData)
admin.site.register(DataEquipment)
admin.site.register(ProfileAltEquipment)
