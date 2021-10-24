from django.contrib import admin
from .models import FazzToolsUser, Alt, Profession, ProfessionTier, ProfessionRecipe, AltProfession, AltProfessionData, Equipment, AltEquipment

# Register your models here.

admin.site.register(FazzToolsUser)
admin.site.register(Alt)
admin.site.register(Profession)
admin.site.register(ProfessionTier)
admin.site.register(ProfessionRecipe)
admin.site.register(AltProfession)
admin.site.register(AltProfessionData)
admin.site.register(Equipment)
admin.site.register(AltEquipment)
