from rest_framework import serializers

from apicore.models import (
    DataEquipment,
    DataEquipmentVariant,
    DataMount,
    DataPet,
    DataProfession,
    DataProfessionRecipe,
    DataProfessionTier,
    DataReagent,
    DataRecipeReagent,
    ProfileAlt,
    ProfileAltEquipment,
    ProfileAltProfession,
    ProfileAltProfessionData,
    ProfileUser,
    ProfileUserMount,
    ProfileUserPet,
)


class DataProfessionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DataProfession
        fields = ("profession_id", "profession_name")


class DataProfessionTierSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DataProfessionTier
        fields = ("tier_id", "tier_name", "profession")


class DataProfessionRecipeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DataProfessionRecipe
        fields = ("recipe_id", "recipe_name", "tier")


class DataReagentSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DataReagent
        fields = ("reagent_id", "reagent_name", "reagent_quality")


class DataRecipeReagentSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DataRecipeReagent
        fields = ("recipe", "reagent", "quantity")


class DataEquipmentSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DataEquipment
        fields = (
            "equipment_id",
            "equipment_name",
            "equipment_type",
            "equipment_slot",
            "equipment_icon",
        )


class DataEquipmentVariantSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DataEquipmentVariant
        fields = (
            "equipment",
            "variant",
            "stamina",
            "armour",
            "strength",
            "agility",
            "intellect",
            "haste",
            "mastery",
            "vers",
            "crit",
            "level",
            "quality",
        )


class DataMountSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DataMount
        fields = (
            "mount_id",
            "mount_name",
            "mount_description",
            "mount_source",
            "mount_media_zoom",
            "mount_media_icon",
            "mount_faction",
        )


class DataPetSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DataPet
        fields = (
            "pet_id",
            "pet_name",
            "pet_description",
            "pet_source",
            "pet_media_icon",
            "pet_faction",
            "pet_npc_id",
        )


class ProfileUserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ProfileUser
        fields = ("user_id", "user_file", "user_last_update")


class ProfileUserMountSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ProfileUserMount
        fields = ("user", "mount")


class ProfileUserPetSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ProfileUserPet
        fields = ("user", "pet")


class ProfileAltSerializer(serializers.HyperlinkedModelSerializer):
    get_alt_class_display = serializers.ReadOnlyField()
    get_alt_race_display = serializers.ReadOnlyField()

    class Meta:
        model = ProfileAlt
        fields = (
            "alt_id",
            "alt_account_id",
            "alt_level",
            "alt_name",
            "alt_realm",
            "alt_realm_id",
            "alt_realm_slug",
            "alt_class",
            "get_alt_class_display",
            "alt_race",
            "get_alt_race_display",
            "alt_gender",
            "alt_faction",
        )


class ProfileAltProfessionSerializer(serializers.ModelSerializer):
    get_profession_1_display = serializers.ReadOnlyField()
    get_profession_2_display = serializers.ReadOnlyField()

    class Meta:
        model = ProfileAltProfession
        fields = (
            "alt",
            "profession_1",
            "get_profession_1_display",
            "profession_2",
            "get_profession_2_display",
        )


class ProfileAltProfessionDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileAltProfessionData
        fields = ("alt", "profession_recipe", "profession_tier", "profession")


class ProfileAltEquipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileAltEquipment
        fields = (
            "alt",
            "head",
            "neck",
            "shoulder",
            "back",
            "chest",
            "tabard",
            "shirt",
            "wrist",
            "hands",
            "belt",
            "legs",
            "feet",
            "ring1",
            "ring2",
            "trinket1",
            "trinket2",
            "weapon1",
            "weapon2",
            "alt_equipment_expiry_date",
        )
