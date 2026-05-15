from django.contrib import admin

from apicore.models import (
    DataEquipment,
    DataProfession,
    DataProfessionRecipe,
    DataProfessionTier,
    ProfileAlt,
    ProfileAltEquipment,
    ProfileAltProfession,
    ProfileAltProfessionData,
    ProfileUser,
)

admin.site.register(ProfileUser)
admin.site.register(ProfileAlt)
admin.site.register(DataProfession)
admin.site.register(DataProfessionTier)
admin.site.register(DataProfessionRecipe)
admin.site.register(ProfileAltProfession)
admin.site.register(ProfileAltProfessionData)
admin.site.register(DataEquipment)
admin.site.register(ProfileAltEquipment)
