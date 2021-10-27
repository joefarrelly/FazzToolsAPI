from rest_framework import serializers
# from .models import FazzToolsUser, Alt, Profession, ProfessionTier, ProfessionRecipe, AltProfession, AltProfessionData, Equipment, EquipmentVariant, AltEquipment
from .models import *


class DataProfessionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DataProfession
        fields = ('professionId', 'professionName')


class DataProfessionTierSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DataProfessionTier
        fields = ('tierId', 'tierName', 'profession')


class DataProfessionRecipeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DataProfessionRecipe
        fields = ('recipeId', 'recipeName', 'professionTier')


class DataReagentSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DataReagent
        fields = ('reagentId', 'reagentName', 'reagentQuality')


class DataRecipeReagentSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DataRecipeReagent
        fields = ('recipe', 'reagent', 'quantity')


class DataEquipmentSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DataEquipment
        fields = ('equipmentId', 'equipmentName', 'equipmentType', 'equipmentSlot', 'equipmentIcon')


class DataEquipmentVariantSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DataEquipmentVariant
        fields = ('equipment', 'variant', 'stamina', 'armour', 'strength', 'agility', 'intellect', 'haste', 'mastery', 'vers', 'crit', 'level', 'quality')


#################################################################################
#                                                                               #
#                            Data/Profile Separator                             #
#                                                                               #
#################################################################################


class ProfileFazzToolsUserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ProfileFazzToolsUser
        fields = ('userId',)


class ProfileAltSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ProfileAlt
        fields = ('altId', 'altLevel', 'altName', 'altRealm', 'altRealmId', 'altRealmSlug', 'altClass', 'get_altClass_display', 'altRace', 'get_altRace_display', 'altGender', 'altFaction')


class ProfileAltProfessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileAltProfession
        fields = ('alt', 'profession1', 'get_profession1_display', 'profession2', 'get_profession2_display')


class ProfileAltProfessionDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileAltProfessionData
        fields = ('alt', 'professionRecipe', 'professionTier', 'profession')


class ProfileAltEquipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileAltEquipment
        fields = ('alt', 'head', 'neck', 'shoulder', 'back', 'chest', 'tabard', 'shirt', 'wrist', 'hands', 'belt', 'legs', 'feet', 'ring1', 'ring2', 'trinket1', 'trinket2', 'weapon1', 'weapon2', 'altEquipmentExpiryDate')
