from django.contrib import admin
from .models import Alt, AltProfession, AltAchievement, AltQuestCompleted, AltMedia, Equipment, AltEquipment

# Register your models here.

admin.site.register(Alt)
admin.site.register(AltProfession)
admin.site.register(AltAchievement)
admin.site.register(AltQuestCompleted)
admin.site.register(AltMedia)
admin.site.register(Equipment)
admin.site.register(AltEquipment)
