from rest_framework import serializers
from .models import Alt, AltProfession


class AltSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Alt
        fields = ('altId', 'altLevel', 'altName', 'altRealm', 'altRealmId', 'altRealmSlug', 'altClass', 'altRace', 'altGender', 'altFaction', 'altExpiryDate')


class AltProfessionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = AltProfession
        fields = ('alt', 'profession', 'professionData', 'altProfessionExpiryDate')
