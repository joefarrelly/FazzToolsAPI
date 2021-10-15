from rest_framework import serializers
from .models import Alt, AltProfession, AltAchievement, AltQuestCompleted, AltMedia, Equipment, AltEquipment


class AltSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Alt
        fields = ('altId', 'altLevel', 'altName', 'altRealm', 'altRealmId', 'altRealmSlug', 'altClass', 'altRace', 'altGender', 'altFaction', 'altExpiryDate')


class AltProfessionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = AltProfession
        fields = ('alt', 'profession', 'professionData', 'altProfessionExpiryDate')


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
