from rest_framework import serializers
from .models import FazzToolsUser, Alt, Profession, ProfessionTier, ProfessionRecipe, AltProfession, AltProfessionData, AltAchievement, AltQuestCompleted, AltMedia, Equipment, AltEquipment


class FazzToolsUserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = FazzToolsUser
        fields = ('userId',)


class AltSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Alt
        fields = ('altId', 'altLevel', 'altName', 'altRealm', 'altRealmId', 'altRealmSlug', 'altClass', 'get_altClass_display', 'altRace', 'get_altRace_display', 'altGender', 'altFaction')


class ProfessionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Profession
        fields = ('professionId', 'professionName')


class ProfessionTierSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ProfessionTier
        fields = ('tierId', 'tierName', 'profession')


class ProfessionRecipeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ProfessionRecipe
        fields = ('recipeId', 'recipeName', 'professionTier')


class AltProfessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AltProfession
        fields = ('alt', 'profession1', 'get_profession1_display', 'profession2', 'get_profession2_display')


class AltProfessionDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = AltProfessionData
        fields = ('alt', 'professionRecipe', 'professionTier', 'profession')


class AltAchievementSerializer(serializers.HyperlinkedModelSerializer):
    alt = serializers.HyperlinkedRelatedField(view_name='alt-detail', queryset=Alt.objects.all())

    class Meta:
        model = AltAchievement
        fields = ('alt', 'achievementData', 'altAchievementExpiryDate')


class AltQuestCompletedSerializer(serializers.HyperlinkedModelSerializer):
    alt = serializers.HyperlinkedRelatedField(view_name='alt-detail', queryset=Alt.objects.all())

    class Meta:
        model = AltQuestCompleted
        fields = ('alt', 'questCompletedData', 'altQuestCompletedExpiryDate')


class AltMediaSerializer(serializers.HyperlinkedModelSerializer):
    alt = serializers.HyperlinkedRelatedField(view_name='alt-detail', queryset=Alt.objects.all())

    class Meta:
        model = AltMedia
        fields = ('alt', 'avatar', 'inset', 'main', 'mainRaw', 'altMediaExpiryDate')


class EquipmentSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Equipment
        fields = ('item_id', 'name', 'slot', 'armour_type', 'icon')


class AltEquipmentSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = AltEquipment
        fields = ('alt', 'equipment', 'item_level', 'stats', 'slot', 'quality', 'sockets', 'enchants', 'spells', 'azerite', 'altEquipmentExpiryDate')
